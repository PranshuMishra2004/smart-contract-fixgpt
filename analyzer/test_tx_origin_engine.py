from analyzer.fixgpt_engine import run_fixgpt


source_file = (
    "contracts/src/VulnerableAuth.sol"
)


result = run_fixgpt(
    source_file=source_file,
    project_root=".",
)


print()
print("=" * 70)
print("TX.ORIGIN FIXGPT RESULT")
print("=" * 70)

print(
    f"Source file: "
    f"{result['source_file']}"
)

print(
    f"Total findings: "
    f"{result['total_findings']}"
)

print(
    f"Actionable findings: "
    f"{result['actionable_findings']}"
)

print(
    f"Skipped findings: "
    f"{result['skipped_findings']}"
)


for index, item in enumerate(
    result["results"],
    start=1,
):

    finding = item["finding"]
    verification = item["verification"]

    print()
    print("-" * 70)

    print(
        f"Finding #{index}"
    )

    print(
        f"Category: "
        f"{finding['category']}"
    )

    print(
        f"Severity: "
        f"{finding['severity']}"
    )

    print(
        f"Candidate: "
        f"{item['candidate_file']}"
    )

    print()
    print("VERIFICATION")

    print(
        f"Compilation: "
        f"{'PASSED' if verification['compile_success'] else 'FAILED'}"
    )

    print(
        f"Slither target vulnerability: "
        f"{'REMOVED' if verification['vulnerability_removed'] else 'STILL DETECTED'}"
    )

    foundry = verification["foundry"]

    if foundry["applicable"]:

        print(
            f"Foundry security test: "
            f"{'PASSED' if foundry['passed'] else 'FAILED'}"
        )

    else:

        print(
            "Foundry security test: "
            "NOT APPLICABLE"
        )

    print(
        f"Overall verification: "
        f"{'PASSED' if verification['verification_passed'] else 'FAILED'}"
    )