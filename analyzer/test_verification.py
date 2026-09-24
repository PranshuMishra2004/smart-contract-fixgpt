from analyzer.verification import verify_fix


project_root = "."

fixed_contract = (
    "reports/generated/VulnerableBank_fixed.sol"
)

result = verify_fix(
    project_root=project_root,
    source_file=fixed_contract,
    target_check="reentrancy-eth",
)

print("=" * 70)
print("FIX VERIFICATION RESULT")
print("=" * 70)

print(f"Compilation successful: {result['compile_success']}")
print(f"Target detector: {result['target_check']}")
print(
    f"Remaining detectors: "
    f"{result['remaining_detectors']}"
)
print(
    f"Vulnerability removed: "
    f"{result['vulnerability_removed']}"
)
print(
    f"Slither report: "
    f"{result['slither_report']}"
)