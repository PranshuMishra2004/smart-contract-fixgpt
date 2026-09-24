import json
import subprocess
from pathlib import Path

from analyzer.security_test_registry import (
    get_security_test,
)


COMMAND_TIMEOUT = 180


def run_command(
    command: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess:
    """
    Run a command with a timeout.
    """

    print(
        f"    Running: {' '.join(command)}"
    )

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Command timed out after "
            f"{COMMAND_TIMEOUT} seconds:\n"
            f"{' '.join(command)}"
        ) from exc

    return result


def compile_contract(
    project_root: str,
    source_file: str,
) -> dict:
    """
    Compile the candidate Solidity contract.
    """

    root = Path(project_root).resolve()
    source_path = Path(source_file)

    if not source_path.is_absolute():
        source_path = root / source_path

    source_path = source_path.resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"Contract not found: {source_path}"
        )

    print(
        "    Compiling candidate contract..."
    )

    result = run_command(
        [
            "solc",
            "--bin",
            str(source_path),
        ],
        root,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Candidate compilation failed.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    print(
        "    Compilation successful."
    )

    return {
        "success": True,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_slither(
    project_root: str,
    source_file: str,
    output_file: str,
) -> dict:
    """
    Run Slither against the candidate contract.
    """

    root = Path(project_root).resolve()
    source_path = Path(source_file)

    if not source_path.is_absolute():
        source_path = root / source_path

    source_path = source_path.resolve()

    output_path = (
        root / output_file
    ).resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"Contract not found: {source_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "    Running Slither re-analysis..."
    )

    result = run_command(
        [
            "slither",
            str(source_path),
            "--compile-force-framework",
            "solc",
            "--json",
            str(output_path),
        ],
        root,
    )

    if not output_path.exists():
        raise RuntimeError(
            "Slither did not create "
            "the expected report.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        report = json.load(file)

    if not report.get("success"):
        raise RuntimeError(
            "Slither report contains "
            f"an error: {report.get('error')}"
        )

    print(
        "    Slither re-analysis completed."
    )

    return report


def get_detector_names(
    slither_report: dict,
) -> list[str]:
    """
    Extract detector names from a Slither report.
    """

    detectors = (
        slither_report
        .get("results", {})
        .get("detectors", [])
    )

    return [
        detector.get("check")
        for detector in detectors
        if detector.get("check")
    ]


def verify_fix(
    project_root: str,
    source_file: str,
    target_check: str,
) -> dict:
    """
    Perform complete verification:

    1. Compilation
    2. Slither re-analysis
    3. Vulnerability-specific security test
    """

    # --------------------------------------------------
    # 1. COMPILATION
    # --------------------------------------------------

    print(
        "    Verification: 1/3 Compilation"
    )

    compile_result = compile_contract(
        project_root,
        source_file,
    )

    # --------------------------------------------------
    # 2. SLITHER
    # --------------------------------------------------

    print(
        "    Verification: 2/3 Static analysis"
    )

    slither_report_file = (
        "reports/generated/"
        "verified_slither.json"
    )

    slither_report = run_slither(
        project_root,
        source_file,
        slither_report_file,
    )

    remaining_detectors = (
        get_detector_names(
            slither_report
        )
    )

    vulnerability_removed = (
        target_check
        not in remaining_detectors
    )

    # --------------------------------------------------
    # 3. SECURITY TEST REGISTRY
    # --------------------------------------------------

    security_test = get_security_test(
        target_check
    )

    security_test_result = {
        "applicable": False,
        "passed": None,
        "message": (
            "No vulnerability-specific "
            "security test is registered "
            "for this detector."
        ),
    }

    if security_test is not None:

        print(
            "    Verification: "
            "3/3 Security test"
        )

        security_test_result = (
            security_test(
                project_root,
                source_file,
            )
        )

    else:

        print(
            "    Verification: "
            "3/3 Security test "
            "not applicable"
        )

    # --------------------------------------------------
    # OVERALL RESULT
    # --------------------------------------------------

    if security_test_result.get(
        "applicable",
        False,
    ):

        verification_passed = (
            compile_result["success"]
            and vulnerability_removed
            and security_test_result["passed"]
        )

    else:

        verification_passed = (
            compile_result["success"]
            and vulnerability_removed
        )

    return {
        "compile_success": (
            compile_result["success"]
        ),
        "target_check": target_check,
        "remaining_detectors": (
            remaining_detectors
        ),
        "vulnerability_removed": (
            vulnerability_removed
        ),
        "foundry": security_test_result,
        "verification_passed": (
            verification_passed
        ),
        "slither_report": (
            slither_report_file
        ),
    }