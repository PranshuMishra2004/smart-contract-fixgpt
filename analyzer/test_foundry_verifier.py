from pathlib import Path

from analyzer.foundry_verifier import (
    run_foundry_reentrancy_test,
)


def main():
    root = Path(
        __file__
    ).resolve().parents[1]

    candidate = (
        root
        / "reports"
        / "generated"
        / "foundry_reentrancy_test.sol"
    )

    candidate.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Known-safe bank contract.
    # State is updated before the external call,
    # which blocks the reentrancy attack.
    source = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract SafeBank {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 amount = balances[msg.sender];

        require(
            amount > 0,
            "No balance"
        );

        balances[msg.sender] = 0;

        (
            bool success,
        ) = msg.sender.call{
            value: amount
        }("");

        require(
            success,
            "Transfer failed"
        );
    }
}
""".strip() + "\n"

    candidate.write_text(
        source,
        encoding="utf-8",
    )

    print(
        "Running Foundry reentrancy verification..."
    )

    result = run_foundry_reentrancy_test(
        project_root=str(root),
        source_file=str(candidate),
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "FOUNDRY REENTRANCY TEST RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Applicable: {result.get('applicable')}"
    )

    print(
        f"Passed: {result.get('passed')}"
    )

    print(
        f"Contract: {result.get('contract')}"
    )

    if result.get("stdout"):
        print("\nSTDOUT:")
        print(result["stdout"])

    if result.get("stderr"):
        print("\nSTDERR:")
        print(result["stderr"])

    if not result.get("passed"):
        raise RuntimeError(
            "Foundry reentrancy verification failed."
        )

    print(
        "\nFoundry reentrancy verification PASSED."
    )


if __name__ == "__main__":
    main()