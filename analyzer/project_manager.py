import shutil
import zipfile
from pathlib import Path
from uuid import uuid4


SUPPORTED_ARCHIVES = {".zip"}
SUPPORTED_SOURCE_FILES = {".sol"}


def create_workspace(
    input_file: str,
    workspace_root: str = "reports/workspaces",
) -> Path:
    """
    Create an isolated workspace from either:

    - a single Solidity file
    - a ZIP archive containing a Solidity project

    The original input file is never modified.
    """

    source_path = Path(input_file)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {source_path}"
        )

    workspace_base = Path(workspace_root)

    workspace_base.mkdir(
        parents=True,
        exist_ok=True,
    )

    workspace = (
        workspace_base
        / uuid4().hex
    )

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    extension = source_path.suffix.lower()

    if extension in SUPPORTED_SOURCE_FILES:

        destination = (
            workspace / source_path.name
        )

        shutil.copy2(
            source_path,
            destination,
        )

        return workspace

    if extension in SUPPORTED_ARCHIVES:

        extract_zip_safely(
            source_path,
            workspace,
        )

        return find_project_root(
            workspace
        )

    raise ValueError(
        "Unsupported file type. "
        "Use a .sol file or .zip archive."
    )


def extract_zip_safely(
    archive_path: Path,
    destination: Path,
) -> None:
    """
    Safely extract a ZIP archive.
    Prevents path traversal and symbolic links.
    """

    destination = destination.resolve()

    with zipfile.ZipFile(
        archive_path,
        "r",
    ) as archive:

        for member in archive.infolist():

            member_name = member.filename
            member_path = Path(member_name)

            if member_path.is_absolute():
                raise ValueError(
                    f"Unsafe archive path: {member_name}"
                )

            target_path = (
                destination / member_path
            ).resolve()

            if not target_path.is_relative_to(
                destination
            ):
                raise ValueError(
                    f"Unsafe archive path: {member_name}"
                )

            file_type = (
                member.external_attr >> 16
            )

            if (
                file_type & 0o170000
            ) == 0o120000:
                raise ValueError(
                    f"Symbolic links are not allowed: "
                    f"{member_name}"
                )

            archive.extract(
                member,
                destination,
            )


def find_project_root(
    workspace: Path,
) -> Path:
    """
    Find the root of a Foundry project.
    """

    workspace = workspace.resolve()

    if (
        workspace / "foundry.toml"
    ).is_file():
        return workspace

    foundry_files = list(
        workspace.rglob("foundry.toml")
    )

    if len(foundry_files) == 1:
        return foundry_files[0].parent

    if len(foundry_files) > 1:
        raise ValueError(
            "Multiple Foundry projects were found "
            "inside the uploaded archive."
        )

    solidity_files = list(
        workspace.rglob("*.sol")
    )

    if solidity_files:
        return workspace

    raise ValueError(
        "No Solidity files were found in the "
        "uploaded project."
    )


def get_analysis_target(
    workspace: Path,
) -> Path:
    """
    Determine what FixGPT should analyze.

    Foundry project:
        analyze the complete directory.

    Single Solidity workspace:
        analyze the single .sol file.
    """

    workspace = workspace.resolve()

    if (
        workspace / "foundry.toml"
    ).is_file():
        return workspace

    solidity_files = list(
        workspace.rglob("*.sol")
    )

    if len(solidity_files) == 1:
        return solidity_files[0]

    if len(solidity_files) == 0:
        raise ValueError(
            "No Solidity source file was found."
        )

    raise ValueError(
        "Multiple Solidity files were found, "
        "but no Foundry project configuration exists."
    )