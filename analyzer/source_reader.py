from pathlib import Path


def read_source_lines(
    source_file: str,
    start_line: int,
    end_line: int,
) -> str:
    """
    Read a specific range of lines from a Solidity source file.

    Line numbers are 1-based.
    """

    path = Path(source_file)

    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        lines = file.readlines()

    if start_line < 1 or end_line > len(lines):
        raise ValueError(
            f"Invalid line range {start_line}-{end_line}. "
            f"File contains {len(lines)} lines."
        )

    selected_lines = lines[start_line - 1:end_line]

    return "".join(
        f"{number}: {line}"
        for number, line in enumerate(
            selected_lines,
            start=start_line,
        )
    )