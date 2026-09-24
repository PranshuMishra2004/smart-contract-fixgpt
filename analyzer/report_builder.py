from datetime import datetime, timezone


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
    }

    report_findings = []

    for finding in findings:

        check = finding.get(
            "check"
        )

        remediation = (
            remediation_by_check.get(check)
        )

        report_item = {
            "check": check,
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

    verified_count = 0

    for finding in report_findings:

        remediation = finding.get(
            "remediation"
        )

        if not remediation:
            continue

        if remediation[
            "verification"
        ]["overall"]:
            verified_count += 1

    return {
        "report_version": "1.0",

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
                engine_result.get(
                    "actionable_findings",
                    0,
                )
            ),
            "skipped_findings": (
                engine_result.get(
                    "skipped_findings",
                    0,
                )
            ),
            "verified_fixes": (
                verified_count
            ),
        },

        "findings": report_findings,
    }