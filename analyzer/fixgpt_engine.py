from pathlib import Path

from analyzer.ai_client import analyze_with_ai
from analyzer.ai_client import repair_with_ai
from analyzer.analysis_runner import run_slither_analysis
from analyzer.diff_generator import generate_code_diff
from analyzer.finding_model import SecurityFinding
from analyzer.fix_applier import apply_function_fix
from analyzer.slither_parser import analyze_report
from analyzer.slither_parser import resolve_source_file
from analyzer.verification import verify_fix


ACTIONABLE_SEVERITIES = {
    "Critical",
    "High",
    "Medium",
}


MAX_AI_FIX_ATTEMPTS = 2


def analyze_contract(
    source_file: str,
    project_root: str = ".",
) -> list[SecurityFinding]:
    """
    Run the initial Slither analysis and parse the
    generated report.

    All report paths are resolved against the isolated
    project workspace so the code works both locally
    and in a deployed container.
    """

    root = Path(project_root).resolve()

    print(
        "Running initial security analysis..."
    )

    report_file = (
        root
        / "reports"
        / "generated"
        / "initial_slither.json"
    ).resolve()

    run_slither_analysis(
        project_root=str(root),
        source_file=str(
            Path(source_file).resolve()
        ),
        report_file=str(report_file),
    )

    print(
        "Initial Slither analysis completed."
    )

    return analyze_report(
        report_file=str(report_file),
        source_root=str(root),
    )

def select_actionable_findings(
    findings: list[SecurityFinding],
) -> list[SecurityFinding]:

    return [
        finding
        for finding in findings
        if finding.severity in ACTIONABLE_SEVERITIES
    ]


def create_candidate(
    finding: SecurityFinding,
    ai_result,
    finding_index: int,
    project_root: str,
) -> Path:
    """
    Create a new candidate Solidity file.
    """

    source_path = resolve_source_file(
        finding.file,
        project_root,
    )

    output_directory = (
        Path(project_root)
        / "reports"
        / "generated"
    ).resolve()

    output_file = (
        output_directory
        / (
            f"{finding.function or 'contract'}"
            f"_fixed_{finding_index}.sol"
        )
    ).resolve()

    return apply_function_fix(
        source_file=str(source_path),
        start_line=finding.start_line,
        end_line=finding.end_line,
        fixed_code=ai_result.fixed_code,
        output_file=str(output_file),
    )


def process_finding(
    finding: SecurityFinding,
    finding_index: int,
    project_root: str = ".",
) -> dict:

    print()
    print(
        f"Processing finding #{finding_index}: "
        f"{finding.category}"
    )

    print(
        f"Severity: {finding.severity}"
    )

    print(
        f"Function: {finding.function}"
    )

    if (
        not finding.file
        or finding.start_line is None
        or finding.end_line is None
    ):
        print(
            "Finding skipped: "
            "source location unavailable."
        )

        return {
            "status": "skipped",
            "reason": (
                "Finding does not map to a "
                "specific source-code range."
            ),
            "finding": finding.to_dict(),
        }

    # --------------------------------------------------
    # AI + COMPILATION RETRY LOOP
    # --------------------------------------------------

    ai_result = None
    candidate_file = None
    compiler_error = None
    attempts = 0

    while attempts < MAX_AI_FIX_ATTEMPTS:

        attempts += 1

        if attempts == 1:

            print(
                "  → Step 1/3: Generating AI remediation..."
            )

            ai_result = analyze_with_ai(
                finding
            )

        else:

            print(
                "  → AI repair attempt "
                f"{attempts}/{MAX_AI_FIX_ATTEMPTS}..."
            )

            ai_result = repair_with_ai(
                finding=finding,
                previous_code=ai_result.fixed_code,
                compiler_error=compiler_error,
            )

        print(
            "  → Step 2/3: Applying AI-generated fix..."
        )

        candidate_file = create_candidate(
            finding=finding,
            ai_result=ai_result,
            finding_index=finding_index,
            project_root=project_root,
        )

        print(
            f"  → Candidate created: "
            f"{candidate_file}"
        )

        source_path = resolve_source_file(
            finding.file,
            project_root,
        )

        # ----------------------------------------------
        # COMPILE ONLY
        # ----------------------------------------------

        print(
            "  → Checking generated code compilation..."
        )

        try:

            from analyzer.verification import (
                compile_contract,
            )

            compile_contract(
                project_root=project_root,
                source_file=str(candidate_file),
            )

            print(
                "  → Candidate compilation passed."
            )

            compiler_error = None
            break

        except RuntimeError as exc:

            compiler_error = str(exc)

            print(
                "  → Candidate compilation failed."
            )

            if attempts >= MAX_AI_FIX_ATTEMPTS:

                print(
                    "  → Maximum AI repair attempts reached."
                )

                return {
                    "status": "failed",
                    "reason": (
                        "AI-generated Solidity "
                        "failed compilation "
                        "after retry."
                    ),
                    "finding": finding.to_dict(),
                    "ai_response": (
                        ai_result.model_dump()
                    ),
                    "candidate_file": str(
                        candidate_file
                    ),
                    "compiler_error": compiler_error,
                    "attempts": attempts,
                }

            print(
                "  → Sending compiler error "
                "back for correction..."
            )

    # --------------------------------------------------
    # CODE DIFF
    # --------------------------------------------------

    print(
        "  → Generating code diff..."
    )

    source_path = resolve_source_file(
        finding.file,
        project_root,
    )

    code_diff = generate_code_diff(
        original_file=str(source_path),
        fixed_file=str(candidate_file),
    )

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print(
        "  → Step 3/3: Verifying generated fix..."
    )

    verification_result = verify_fix(
        project_root=project_root,
        source_file=str(candidate_file),
        target_check=finding.check,
    )

    print(
        "  → Verification completed."
    )

    return {
        "status": "processed",
        "finding": finding.to_dict(),
        "ai_response": ai_result.model_dump(),
        "candidate_file": str(candidate_file),
        "code_diff": code_diff,
        "compiler_repair_attempts": attempts,
        "verification": verification_result,
    }


def run_fixgpt(
    source_file: str,
    project_root: str = ".",
) -> dict:

    findings = analyze_contract(
        source_file=source_file,
        project_root=project_root,
    )

    actionable_findings = (
        select_actionable_findings(
            findings
        )
    )

    print()

    print(
        f"Total findings discovered: "
        f"{len(findings)}"
    )

    print(
        f"Actionable findings: "
        f"{len(actionable_findings)}"
    )

    print(
        f"Skipped findings: "
        f"{len(findings) - len(actionable_findings)}"
    )

    results = []

    for index, finding in enumerate(
        actionable_findings,
        start=1,
    ):
        result = process_finding(
            finding=finding,
            finding_index=index,
            project_root=project_root,
        )

        results.append(result)

    return {
        "source_file": source_file,
        "project_root": project_root,
        "total_findings": len(findings),
        "actionable_findings": len(
            actionable_findings
        ),
        "skipped_findings": (
            len(findings)
            - len(actionable_findings)
        ),
        "findings": [
            finding.to_dict()
            for finding in findings
        ],
        "results": results,
    }