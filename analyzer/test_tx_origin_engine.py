from pathlib import Path

from analyzer.fixgpt_engine import (
    run_fixgpt,
)


def main():
    root = Path(
        __file__
    ).resolve().parents[1]

    source_file = (
        root
        / "contracts"
        / "src"
        / "VulnerableAuth.sol"
    )

    print(
        "Running FixGPT tx-origin engine test..."
    )

    result = run_fixgpt(
        source_file=str(source_file),
        project_root=str(root),
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TX.ORIGIN FIXGPT RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Source file: {source_file}"
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

    # run_fixgpt() returns findings as dictionaries.
    tx_origin_findings = [
        finding
        for finding in result["findings"]
        if finding.get("check") == "tx-origin"
    ]

    if not tx_origin_findings:
        raise RuntimeError(
            "The tx-origin detector was not found "
            "in VulnerableAuth.sol."
        )

    print(
        f"\nDetected tx-origin findings: "
        f"{len(tx_origin_findings)}"
    )

    for index, item in enumerate(
        result["results"],
        start=1,
    ):
        print(
            "\n"
            + "-" * 70
        )

        print(
            f"Actionable finding #{index}"
        )

        finding = item.get(
            "finding"
        )

        if isinstance(finding, dict):
            print(
                f"Detector: "
                f"{finding.get('check', 'Unknown')}"
            )

            print(
                f"Category: "
                f"{finding.get('category', 'Unknown')}"
            )

            print(
                f"Severity: "
                f"{finding.get('severity', 'Unknown')}"
            )

        verification = (
            item.get(
                "verification"
            )
            or {}
        )

        if verification:

            print(
                f"Compilation: "
                f"{'PASSED' if verification.get('compile_success') else 'FAILED'}"
            )

            print(
                f"Slither target: "
                f"{'REMOVED' if verification.get('vulnerability_removed') else 'STILL DETECTED'}"
            )

            foundry = verification.get(
                "foundry",
                {},
            )

            if foundry.get(
                "applicable"
            ):
                print(
                    f"Foundry security test: "
                    f"{'PASSED' if foundry.get('passed') else 'FAILED'}"
                )

            print(
                f"Overall verification: "
                f"{'PASSED' if verification.get('verification_passed') else 'FAILED'}"
            )

    print(
        "\nTx-origin engine test completed."
    )


if __name__ == "__main__":
    main()