from datetime import datetime, timezone


ACTIONABLE_SEVERITIES = {
    "Critical",
    "High",
    "Medium",
}


SEVERITY_PENALTIES = {
    "Critical": 30,
    "High": 20,
    "Medium": 10,
    "Low": 5,
    "Informational": 0,
}


def calculate_project_score(
    report_findings: list[dict],
) -> int:
    """
    Calculate a security score from 0 to 100.

    Verified remediations receive no penalty.

    Unresolved actionable findings receive a penalty
    based on severity.

    Informational findings do not reduce the score.
    """

    score = 100

    for finding in report_findings:

        severity = (
            finding.get("severity")
            or "Informational"
        )

        remediation = finding.get(
            "remediation"
        )

        # A successfully verified remediation
        # contributes no security penalty.
        if (
            remediation
            and remediation.get(
                "verification",
                {}
            ).get(
                "overall",
                False,
            )
        ):
            continue

        penalty = SEVERITY_PENALTIES.get(
            severity,
            0,
        )

        score -= penalty

    return max(
        0,
        min(
            100,
            score,
        ),
    )


def calculate_project_status(
    actionable_findings: int,
    verified_fixes: int,
) -> str:
    """
    Determine the overall project status.

    PASS means every actionable finding has a
    verified remediation.

    FAIL means at least one actionable finding
    remains unverified.
    """

    if actionable_findings == 0:
        return "PASS"

    if verified_fixes >= actionable_findings:
        return "PASS"

    return "FAIL"


def build_security_report(
    engine_result: dict,
) -> dict:
    """
    Convert the internal FixGPT engine result into
    a clean report for the API and frontend.
    """

    findings = engine_result.get(
        "findings",
        [],
    )

    results = engine_result.get(
        "results",
        [],
    )

    remediation_by_check = {
        result["finding"]["check"]: result
        for result in results
        if result.get("status") == "processed"
        and result.get("finding")
    }

    report_findings = []

    for finding in findings:

        check = finding.get(
            "check"
        )

        remediation = (
            remediation_by_check.get(
                check
            )
        )

        report_item = {
            "check": check,

            # Human-readable title.
            "category": finding.get(
                "category"
            ),

            "severity": finding.get(
                "severity"
            ),

            "confidence": finding.get(
                "confidence"
            ),

            "description": finding.get(
                "description"
            ),

            "resolution": finding.get(
                "resolution",
                (
                    "Review the Slither finding and "
                    "apply the detector-specific "
                    "security mitigation."
                ),
            ),

            "function": finding.get(
                "function"
            ),

            "file": finding.get(
                "file"
            ),

            "start_line": finding.get(
                "start_line"
            ),

            "end_line": finding.get(
                "end_line"
            ),

            "source_code": finding.get(
                "source_code"
            ),

            "source": finding.get(
                "source",
                "Slither",
            ),

            "remediation": None,
        }

        if remediation:

            verification = remediation.get(
                "verification",
                {},
            )

            report_item["remediation"] = {
                "status": "processed",

                "explanation": (
                    remediation[
                        "ai_response"
                    ].get(
                        "explanation"
                    )
                ),

                "root_cause": (
                    remediation[
                        "ai_response"
                    ].get(
                        "root_cause"
                    )
                ),

                "recommendation": (
                    remediation[
                        "ai_response"
                    ].get(
                        "recommendation"
                    )
                ),

                "fixed_code": (
                    remediation[
                        "ai_response"
                    ].get(
                        "fixed_code"
                    )
                ),

                "code_diff": (
                    remediation.get(
                        "code_diff",
                        "",
                    )
                ),

                "candidate_file": (
                    remediation.get(
                        "candidate_file"
                    )
                ),

                "verification": {
                    "compilation": (
                        verification.get(
                            "compile_success",
                            False,
                        )
                    ),

                    "slither": (
                        verification.get(
                            "vulnerability_removed",
                            False,
                        )
                    ),

                    "foundry": (
                        verification.get(
                            "foundry",
                            {},
                        )
                    ),

                    "overall": (
                        verification.get(
                            "verification_passed",
                            False,
                        )
                    ),

                    "remaining_detectors": (
                        verification.get(
                            "remaining_detectors",
                            [],
                        )
                    ),
                },
            }

        report_findings.append(
            report_item
        )

    # --------------------------------------------------
    # VERIFIED FIX COUNT
    # --------------------------------------------------

    verified_count = 0

    for finding in report_findings:

        remediation = finding.get(
            "remediation"
        )

        if not remediation:
            continue

        if (
            remediation[
                "verification"
            ].get(
                "overall",
                False,
            )
        ):
            verified_count += 1

    actionable_findings = (
        engine_result.get(
            "actionable_findings",
            0,
        )
    )

    skipped_findings = (
        engine_result.get(
            "skipped_findings",
            0,
        )
    )

    # --------------------------------------------------
    # PROJECT SCORE + STATUS
    # --------------------------------------------------

    project_score = (
        calculate_project_score(
            report_findings
        )
    )

    project_status = (
        calculate_project_status(
            actionable_findings,
            verified_count,
        )
    )

    return {
        "report_version": "1.1",

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "source_file": (
            engine_result.get(
                "source_file"
            )
        ),

        "summary": {
            "total_findings": len(
                findings
            ),

            "actionable_findings": (
                actionable_findings
            ),

            "skipped_findings": (
                skipped_findings
            ),

            "verified_fixes": (
                verified_count
            ),

            "project_score": (
                project_score
            ),

            "status": (
                project_status
            ),
        },

        "project": {
            "score": project_score,
            "status": project_status,
        },

        "findings": report_findings,
    }