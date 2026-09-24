from analyzer.foundry_verifier import (
    run_foundry_reentrancy_test,
)


result = run_foundry_reentrancy_test(
    project_root=".",
    candidate_file=(
        "reports/generated/withdraw_fixed_1.sol"
    ),
)

print("=" * 70)
print("FOUNDRY SECURITY TEST RESULT")
print("=" * 70)

print(
    f"Contract: {result.get('contract')}"
)

print(
    f"Test passed: {result.get('passed')}"
)

if not result.get("success"):
    print()
    print("STDOUT:")
    print(result.get("stdout"))

    print()
    print("STDERR:")
    print(result.get("stderr"))