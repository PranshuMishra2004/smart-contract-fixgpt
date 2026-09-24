import re
import shutil
import subprocess
from pathlib import Path


def find_contract_name(source_code: str) -> str:
    """
    Find a Solidity contract containing a withdraw function.
    """

    matches = re.finditer(
        r"\bcontract\s+([A-Za-z_][A-Za-z0-9_]*)",
        source_code,
    )

    for match in matches:
        contract_name = match.group(1)

        if "function withdraw" in source_code:
            return contract_name

    raise ValueError(
        "Could not find a Solidity contract with a withdraw function."
    )


def run_foundry_reentrancy_test(
    project_root: str,
    candidate_file: str,
) -> dict:
    """
    Run a Foundry test against a candidate contract to verify
    that a reentrancy attack is blocked.
    """

    root = Path(project_root)
    candidate_path = root / candidate_file

    if not candidate_path.exists():
        raise FileNotFoundError(
            f"Candidate contract not found: {candidate_path}"
        )

    source_code = candidate_path.read_text(
        encoding="utf-8"
    )

    contract_name = find_contract_name(
        source_code
    )

    generated_src_dir = (
        root / "contracts" / "src" / "generated"
    )

    generated_test_dir = (
        root / "contracts" / "test" / "generated"
    )

    generated_src_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_test_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_contract = (
        generated_src_dir / candidate_path.name
    )

    generated_test = (
        generated_test_dir
        / "ReentrancyFixVerification.t.sol"
    )

    shutil.copy2(
        candidate_path,
        generated_contract,
    )

    test_source = f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {{Test}} from "forge-std/Test.sol";
import {{ {contract_name} }} from "../../src/generated/{candidate_path.name}";


contract ReentrancyAttacker {{

    {contract_name} public bank;

    constructor(address bankAddress) {{
        bank = {contract_name}(bankAddress);
    }}

    receive() external payable {{
        bank.withdraw();
    }}

    function attack() external {{
        bank.deposit{{value: 1 ether}}();
        bank.withdraw();
    }}
}}


contract ReentrancyFixVerification is Test {{

    {contract_name} public bank;
    ReentrancyAttacker public attacker;

    function setUp() public {{
        vm.deal(address(this), 100 ether);

        bank = new {contract_name}();

        attacker = new ReentrancyAttacker(
            address(bank)
        );

        vm.deal(
            address(attacker),
            1 ether
        );

        bank.deposit{{value: 10 ether}}();
    }}

    function testReentrancyAttackIsBlocked() public {{
        vm.expectRevert();

        attacker.attack();

        assertEq(
            address(bank).balance,
            10 ether
        );
    }}
}}
""".strip()

    generated_test.write_text(
        test_source + "\n",
        encoding="utf-8",
    )

    try:
        print(
            "    Running Foundry reentrancy test..."
        )

        result = subprocess.run(
            [
                "forge",
                "test",
                "--match-path",
                "test/generated/ReentrancyFixVerification.t.sol",
                "-vv",
            ],
            cwd=root / "contracts",
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            return {
                "applicable": True,
                "success": False,
                "passed": False,
                "contract": contract_name,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return {
            "applicable": True,
            "success": True,
            "passed": True,
            "contract": contract_name,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired as exc:
        return {
            "applicable": True,
            "success": False,
            "passed": False,
            "contract": contract_name,
            "stdout": "",
            "stderr": (
                "Foundry test timed out after 120 seconds."
            ),
        }

    finally:
        if generated_contract.exists():
            generated_contract.unlink()

        if generated_test.exists():
            generated_test.unlink()