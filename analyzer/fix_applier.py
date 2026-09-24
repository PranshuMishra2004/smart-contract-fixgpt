from pathlib import Path


def clean_fixed_code(fixed_code: str) -> str:
    """
    Remove Markdown code fences if the AI accidentally includes them.
    """

    code = fixed_code.strip()

    if code.startswith("```solidity"):
        code = code[len("```solidity"):].strip()

    elif code.startswith("```"):
        code = code[3:].strip()

    if code.endswith("```"):
        code = code[:-3].strip()

    return code


def apply_function_fix(
    source_file: str,
    start_line: int,
    end_line: int,
    fixed_code: str,
    output_file: str,
) -> Path:
    """
    Replace a specific source-code range with AI-generated fixed code.

    The original source file is never modified.
    """

    source_path = Path(source_file)
    output_path = Path(output_file)

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    if start_line < 1 or end_line < start_line:
        raise ValueError(
            f"Invalid line range: {start_line}-{end_line}"
        )

    with source_path.open("r", encoding="utf-8") as file:
        lines = file.readlines()

    if end_line > len(lines):
        raise ValueError(
            f"End line {end_line} exceeds file length {len(lines)}"
        )

    fixed_code = clean_fixed_code(fixed_code)

    # Convert the fixed code into lines.
    replacement_lines = [
        line + "\n" if not line.endswith("\n") else line
        for line in fixed_code.splitlines()
    ]

    # Replace only the affected lines.
    new_lines = (
        lines[: start_line - 1]
        + replacement_lines
        + lines[end_line:]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        file.writelines(new_lines)

    return output_path
    