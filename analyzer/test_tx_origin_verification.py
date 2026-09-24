from analyzer.foundry_verifier import (
    run_foundry_tx_origin_test,
)


result = run_foundry_tx_origin_test(
    project_root=".",
    candidate_file=(
        "reports/generated/"
        "VulnerableAuth_fixed.sol"
    ),
)


print("=" * 70)
print("TX.ORIGIN FOUNDRY VERIFICATION")
print("=" * 70)

print(
    f"Contract: "
    f"{result.get('contract')}"
)

print(
    f"Test passed: "
    f"{result.get('passed')}"
)

if not result.get("success"):
    print()
    print("STDOUT:")
    print(result.get("stdout"))

    print()
    print("STDERR:")
    print(result.get("stderr"))