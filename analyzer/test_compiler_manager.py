import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from analyzer.compiler_manager import (
    get_solc_env_for_source,
    select_compiler_version,
)


def main():
    test_cases = {
        "exact": (
            "pragma solidity 0.8.28;"
        ),
        "caret": (
            "pragma solidity ^0.8.28;"
        ),
        "range": (
            "pragma solidity >=0.8.28 <0.9.0;"
        ),
    }

    with TemporaryDirectory() as temp_dir:

        root = Path(temp_dir)

        for name, pragma in test_cases.items():

            source_file = (
                root / f"{name}.sol"
            )

            source_file.write_text(
                f"""
                // SPDX-License-Identifier: MIT
                {pragma}

                contract CompilerTest {{
                    uint256 public value;
                }}
                """,
                encoding="utf-8",
            )

            version = (
                select_compiler_version(
                    source_file
                )
            )

            print(
                f"{name}: {version}"
            )

        exact_file = (
            root / "exact-runtime.sol"
        )

        exact_file.write_text(
            """
            // SPDX-License-Identifier: MIT
            pragma solidity 0.8.28;

            contract ExactCompilerTest {
                uint256 public value;
            }
            """,
            encoding="utf-8",
        )

        environment = (
            get_solc_env_for_source(
                exact_file
            )
        )

        result = subprocess.run(
            [
                "solc",
                "--version",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr
            )

        print(
            result.stdout
        )

        if "0.8.28" not in result.stdout:
            raise RuntimeError(
                "solc did not use 0.8.28."
            )

        print(
            "Compiler manager test PASSED."
        )


if __name__ == "__main__":
    main()