import difflib
from pathlib import Path


def generate_code_diff(
    original_file: str,
    fixed_file: str,
) -> str:
    """
    Generate a unified diff between the original
    Solidity file and the AI-generated candidate.
    """

    original_path = Path(original_file)
    fixed_path = Path(fixed_file)

    if not original_path.exists():
        raise FileNotFoundError(
            f"Original file not found: {original_path}"
        )

    if not fixed_path.exists():
        raise FileNotFoundError(
            f"Fixed file not found: {fixed_path}"
        )

    original_lines = original_path.read_text(
        encoding="utf-8"
    ).splitlines(keepends=True)

    fixed_lines = fixed_path.read_text(
        encoding="utf-8"
    ).splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=str(original_path),
        tofile=str(fixed_path),
    )

    return "".join(diff)