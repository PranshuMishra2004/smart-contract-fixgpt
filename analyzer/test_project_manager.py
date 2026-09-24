from pathlib import Path

from analyzer.project_manager import create_workspace


source_file = (
    "contracts/src/VulnerableBank.sol"
)

workspace = create_workspace(
    source_file
)

print("=" * 70)
print("PROJECT WORKSPACE TEST")
print("=" * 70)

print(
    f"Workspace: {workspace}"
)

print(
    f"Workspace exists: "
    f"{workspace.exists()}"
)

print(
    "Files:"
)

for path in workspace.rglob("*"):
    if path.is_file():
        print(
            f" - {path}"
        )