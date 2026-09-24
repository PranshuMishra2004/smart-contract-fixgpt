from analyzer.analysis_runner import run_slither_analysis


report = run_slither_analysis(
    project_root=".",
    source_file="contracts",
    report_file=(
        "reports/generated/project_slither.json"
    ),
)

detectors = (
    report
    .get("results", {})
    .get("detectors", [])
)

print()
print("=" * 70)
print("FOUNDRY PROJECT ANALYSIS")
print("=" * 70)

print(
    f"Findings: {len(detectors)}"
)

for detector in detectors:
    print(
        f"- {detector.get('check')} "
        f"({detector.get('impact')})"
    )