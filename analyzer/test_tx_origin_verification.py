from pathlib import Path

from analyzer.foundry_verifier import (
    run_foundry_tx_origin_test,
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

    source = source_file.read_text(
        encoding="utf-8"
    )

    # Create a known-fixed candidate.
    fixed_source = source.replace(
        "tx.origin == owner",
        "msg.sender == owner",
    )

    candidate = (
        root
        / "reports"
        / "generated"
        / "tx_origin_fixed_test.sol"
    )

    candidate.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidate.write_text(
        fixed_source,
        encoding="utf-8",
    )

    print(
        "Running tx-origin Foundry verification..."
    )

    result = run_foundry_tx_origin_test(
        str(root),
        str(candidate),
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TX.ORIGIN SECURITY TEST RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Applicable: {result['applicable']}"
    )

    print(
        f"Passed: {result['passed']}"
    )

    print(
        f"Contract: {result['contract']}"
    )

    if result["stdout"]:
        print("\nSTDOUT:")
        print(result["stdout"])

    if result["stderr"]:
        print("\nSTDERR:")
        print(result["stderr"])

    if not result["passed"]:
        raise RuntimeError(
            "tx-origin Foundry verification failed."
        )

    print(
        "\nTx-origin verification PASSED."
    )


if __name__ == "__main__":
    main()