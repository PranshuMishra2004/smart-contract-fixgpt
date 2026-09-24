from analyzer.analysis_runner import (
    run_slither_analysis,
)


report = run_slither_analysis(
    project_root=".",
    source_file=(
        "contracts/src/VulnerableAuth.sol"
    ),
    report_file=(
        "reports/generated/"
        "tx_origin_slither.json"
    ),
)


detectors = (
    report
    .get("results", {})
    .get("detectors", [])
)


print("=" * 70)
print("TX.ORIGIN DETECTION")
print("=" * 70)

print(
    f"Findings: {len(detectors)}"
)

for detector in detectors:
    print(
        f"- {detector.get('check')} "
        f"({detector.get('impact')})"
    )

    print(
        f"  Confidence: "
        f"{detector.get('confidence')}"
    )

    print()