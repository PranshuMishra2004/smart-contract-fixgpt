import json
import os
import subprocess
from pathlib import Path

from analyzer.compiler_manager import (
    get_solc_env_for_source,
)


COMMAND_TIMEOUT = 120


def run_slither_analysis(
    project_root: str,
    source_file: str,
    report_file: str,
) -> dict:
    """
    Run Slither against either:

    1. A single Solidity file.
    2. A complete Solidity/Foundry project directory.

    Standalone Solidity files use the compiler version
    declared by their pragma.

    Foundry projects are compiled through their project
    configuration.
    """

    root = Path(
        project_root
    ).resolve()

    target = Path(
        source_file
    )

    if not target.is_absolute():
        target = root / target

    target = target.resolve()

    if not target.exists():
        raise FileNotFoundError(
            f"Analysis target not found: {target}"
        )

    report_path = (
        root / report_file
    ).resolve()

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    solc_environment = None

    # --------------------------------------------------
    # SINGLE SOLIDITY FILE
    # --------------------------------------------------

    if target.is_file():

        solc_environment = (
            get_solc_env_for_source(
                target
            )
        )

        command = [
            "slither",
            str(target),
            "--compile-force-framework",
            "solc",
            "--solc",
            "solc",
            "--json",
            str(report_path),
        ]

    # --------------------------------------------------
    # COMPLETE PROJECT DIRECTORY
    # --------------------------------------------------

    elif target.is_dir():

        command = [
            "slither",
            str(target),
            "--json",
            str(report_path),
        ]

    else:

        raise ValueError(
            f"Unsupported analysis target: {target}"
        )

    print(
        f"Running Slither analysis on: {target}"
    )

    print(
        f"Command: {' '.join(command)}"
    )

    try:

        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            env=solc_environment
            if solc_environment is not None
            else os.environ.copy(),
        )

    except subprocess.TimeoutExpired as exc:

        raise RuntimeError(
            "Slither analysis timed out after "
            f"{COMMAND_TIMEOUT} seconds."
        ) from exc

    # Slither can return a non-zero exit code when
    # findings exist, so the exit code alone is not
    # considered a failure.

    if not report_path.exists():

        raise RuntimeError(
            "Slither did not create the expected report.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    with report_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        report = json.load(
            file
        )

    if not report.get("success"):

        raise RuntimeError(
            "Slither analysis failed.\n\n"
            f"Error: {report.get('error')}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    detectors = (
        report
        .get("results", {})
        .get("detectors", [])
    )

    print(
        "Slither analysis completed: "
        f"{len(detectors)} findings"
    )

    return report