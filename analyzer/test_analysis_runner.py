from analyzer.analysis_runner import run_slither_analysis


project_root = "."

source_file = (
    "contracts/src/VulnerableBank.sol"
)

report_file = (
    "reports/generated/initial_slither.json"
)

report = run_slither_analysis(
    project_root=project_root,
    source_file=source_file,
    report_file=report_file,
)

detectors = (
    report
    .get("results", {})
    .get("detectors", [])
)

print("=" * 70)
print("INITIAL SLITHER ANALYSIS")
print("=" * 70)

print(f"Findings: {len(detectors)}")

for detector in detectors:
    print(
        f"- {detector.get('check')} "
        f"({detector.get('impact')})"
    )