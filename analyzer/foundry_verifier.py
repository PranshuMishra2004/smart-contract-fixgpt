from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from analyzer.compiler_manager import (
    select_compiler_version,
)


COMMAND_TIMEOUT = 180

CONTRACT_PATTERN = re.compile(
    r"\bcontract\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)


def find_contract_name(
    source_file: str | Path,
) -> str:
    source_path = Path(
        source_file
    ).resolve()

    source = source_path.read_text(
        encoding="utf-8"
    )

    matches = CONTRACT_PATTERN.findall(
        source
    )

    if not matches:
        raise RuntimeError(
            f"Could not determine contract name "
            f"from {source_path}"
        )

    return matches[0]


def create_temp_foundry_project(
    project_root: str,
    source_file: str,
) -> tuple[
    tempfile.TemporaryDirectory,
    Path,
    str,
]:
    root = Path(
        project_root
    ).resolve()

    source_path = Path(
        source_file
    )

    if not source_path.is_absolute():
        source_path = (
            root / source_path
        )

    source_path = source_path.resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"Contract not found: {source_path}"
        )

    temp_dir = tempfile.TemporaryDirectory(
        prefix="fixgpt_foundry_",
        dir=root,
    )

    project_dir = Path(
        temp_dir.name
    )

    src_dir = project_dir / "src"
    test_dir = project_dir / "test"

    src_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    candidate_path = (
        src_dir / "Candidate.sol"
    )

    shutil.copy2(
        source_path,
        candidate_path,
    )

    contract_name = find_contract_name(
        source_path
    )

    return (
        temp_dir,
        candidate_path,
        contract_name,
    )


def write_foundry_config(
    project_dir: Path,
    compiler_version: str,
) -> None:
    config = f"""
[profile.default]
src = "src"
test = "test"
out = "out"
libs = []
solc_version = "{compiler_version}"
""".strip() + "\n"

    (
        project_dir / "foundry.toml"
    ).write_text(
        config,
        encoding="utf-8",
    )


def run_forge_test(
    project_dir: Path,
    test_name: str,
) -> subprocess.CompletedProcess:
    command = [
        "forge",
        "test",
        "--match-test",
        test_name,
    ]

    print(
        f"    Running Foundry test: "
        f"{test_name}"
    )

    try:
        return subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Foundry test timed out after "
            f"{COMMAND_TIMEOUT} seconds."
        ) from exc


def run_foundry_reentrancy_test(
    project_root: str,
    source_file: str,
) -> dict:
    """
    Verify that a candidate bank contract
    blocks a reentrancy attack.
    """

    temp_dir = None

    try:
        (
            temp_dir,
            candidate_path,
            contract_name,
        ) = create_temp_foundry_project(
            project_root,
            source_file,
        )

        project_dir = Path(
            temp_dir.name
        )

        compiler_version = (
            select_compiler_version(
                candidate_path
            )
        )

        write_foundry_config(
            project_dir,
            compiler_version,
        )

        test_source = f"""
// SPDX-License-Identifier: MIT
pragma solidity {compiler_version};

import "../src/Candidate.sol";

interface Vm {{
    function deal(
        address who,
        uint256 newBalance
    ) external;
}}

interface IBank {{
    function deposit() external payable;
    function withdraw() external;
}}

contract ReentrancyAttacker {{
    IBank public target;
    bool internal entered;

    constructor(
        IBank _target
    ) {{
        target = _target;
    }}

    function deposit()
        external
        payable
    {{
        target.deposit{{
            value: msg.value
        }}();
    }}

    function attack()
        external
    {{
        target.withdraw();
    }}

    receive() external payable {{
        if (!entered) {{
            entered = true;
            target.withdraw();
        }}
    }}
}}

contract SecurityTest {{
    Vm constant vm =
        Vm(
            address(
                uint160(
                    uint256(
                        keccak256(
                            "hevm cheat code"
                        )
                    )
                )
            )
        );

    function testReentrancyBlocked()
        external
    {{
        {contract_name} target =
            new {contract_name}();

        ReentrancyAttacker attacker =
            new ReentrancyAttacker(
                IBank(address(target))
            );

        vm.deal(
            address(attacker),
            1 ether
        );

        attacker.deposit{{
            value: 1 ether
        }}();

        vm.deal(
            address(target),
            2 ether
        );

        uint256 balanceBefore =
            address(target).balance;

        (
            bool success,
        ) = address(attacker).call(
            abi.encodeWithSignature(
                "attack()"
            )
        );

        require(
            !success,
            "Reentrancy attack succeeded"
        );

        require(
            address(target).balance
                == balanceBefore,
            "Target balance changed"
        );
    }}
}}
""".strip() + "\n"

        test_file = (
            project_dir
            / "test"
            / "SecurityTest.t.sol"
        )

        test_file.write_text(
            test_source,
            encoding="utf-8",
        )

        result = run_forge_test(
            project_dir,
            "testReentrancyBlocked",
        )

        return {
            "applicable": True,
            "success": result.returncode == 0,
            "passed": result.returncode == 0,
            "contract": contract_name,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except Exception as exc:
        return {
            "applicable": True,
            "success": False,
            "passed": False,
            "contract": Path(
                source_file
            ).stem,
            "stdout": "",
            "stderr": str(exc),
        }

    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def run_foundry_tx_origin_test(
    project_root: str,
    source_file: str,
) -> dict:
    """
    Verify that a candidate authentication
    contract blocks an intermediary contract
    from bypassing authorization.
    """

    temp_dir = None

    try:
        (
            temp_dir,
            candidate_path,
            contract_name,
        ) = create_temp_foundry_project(
            project_root,
            source_file,
        )

        project_dir = Path(
            temp_dir.name
        )

        compiler_version = (
            select_compiler_version(
                candidate_path
            )
        )

        write_foundry_config(
            project_dir,
            compiler_version,
        )

        test_source = f"""
// SPDX-License-Identifier: MIT
pragma solidity {compiler_version};

import "../src/Candidate.sol";

interface Vm {{
    function startPrank(
        address msgSender,
        address txOrigin
    ) external;

    function stopPrank()
        external;
}}

interface IAuth {{
    function changeBeneficiary(
        address newBeneficiary
    ) external;

    function beneficiary()
        external
        view
        returns (address);
}}

contract OriginAttacker {{
    function attack(
        IAuth target,
        address newBeneficiary
    ) external {{
        target.changeBeneficiary(
            newBeneficiary
        );
    }}
}}

contract SecurityTest {{
    Vm constant vm =
        Vm(
            address(
                uint160(
                    uint256(
                        keccak256(
                            "hevm cheat code"
                        )
                    )
                )
            )
        );

    function testTxOriginBlocked()
        external
    {{
        address owner =
            address(0x1001);

        vm.startPrank(
            owner,
            owner
        );

        {contract_name} target =
            new {contract_name}();

        vm.stopPrank();

        OriginAttacker attacker =
            new OriginAttacker();

        address maliciousBeneficiary =
            address(0xBEEF);

        vm.startPrank(
            owner,
            owner
        );

        (
            bool success,
        ) = address(attacker).call(
            abi.encodeWithSelector(
                OriginAttacker.attack.selector,
                IAuth(address(target)),
                maliciousBeneficiary
            )
        );

        vm.stopPrank();

        require(
            !success,
            "tx.origin authorization succeeded"
        );

        require(
            IAuth(address(target))
                .beneficiary()
                == owner,
            "Beneficiary changed"
        );
    }}
}}
""".strip() + "\n"

        test_file = (
            project_dir
            / "test"
            / "SecurityTest.t.sol"
        )

        test_file.write_text(
            test_source,
            encoding="utf-8",
        )

        result = run_forge_test(
            project_dir,
            "testTxOriginBlocked",
        )

        return {
            "applicable": True,
            "success": result.returncode == 0,
            "passed": result.returncode == 0,
            "contract": contract_name,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except Exception as exc:
        return {
            "applicable": True,
            "success": False,
            "passed": False,
            "contract": Path(
                source_file
            ).stem,
            "stdout": "",
            "stderr": str(exc),
        }

    finally:
        if temp_dir is not None:
            temp_dir.cleanup()