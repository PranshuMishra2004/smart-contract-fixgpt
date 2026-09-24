from analyzer.fixgpt_engine import run_fixgpt
from analyzer.report_builder import build_security_report


source_file = (
    "contracts/src/VulnerableBank.sol"
)


engine_result = run_fixgpt(
    source_file=source_file,
    project_root=".",
)


report = build_security_report(
    engine_result
)


print()
print("=" * 70)
print("FIXGPT SECURITY REPORT")
print("=" * 70)

print(
    f"Report version: "
    f"{report['report_version']}"
)

print(
    f"Generated at: "
    f"{report['generated_at']}"
)

print(
    f"Source file: "
    f"{report['source_file']}"
)

print()
print("SUMMARY")

print(
    f"Total findings: "
    f"{report['summary']['total_findings']}"
)

print(
    f"Actionable findings: "
    f"{report['summary']['actionable_findings']}"
)

print(
    f"Skipped findings: "
    f"{report['summary']['skipped_findings']}"
)

print(
    f"Verified fixes: "
    f"{report['summary']['verified_fixes']}"
)

for index, finding in enumerate(
    report["findings"],
    start=1,
):

    print()
    print("-" * 70)

    print(
        f"Finding #{index}: "
        f"{finding['category']}"
    )

    print(
        f"Severity: "
        f"{finding['severity']}"
    )

    remediation = (
        finding["remediation"]
    )

    if remediation:

        print(
            "Remediation: Available"
        )

        print(
            "Verification: "
            f"{'PASSED' if remediation['verification']['overall'] else 'FAILED'}"
        )

    else:

        print(
            "Remediation: Not generated"
        )