from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


DEFAULT_SOLC_VERSION = os.getenv(
    "FIXGPT_DEFAULT_SOLC_VERSION",
    "0.8.33",
)

COMMAND_TIMEOUT = 120


PRAGMA_PATTERN = re.compile(
    r"\bpragma\s+solidity\s+([^;]+);",
    re.IGNORECASE,
)

VERSION_TOKEN_PATTERN = re.compile(
    r"^(?P<operator>\^|~|>=|<=|>|<|=)?"
    r"\s*v?"
    r"(?P<major>\d+)"
    r"(?:\.(?P<minor>\d+|x|\*))?"
    r"(?:\.(?P<patch>\d+|x|\*))?$",
    re.IGNORECASE,
)


Version = tuple[int, int, int]
Constraint = tuple[str, Version]


def format_version(version: Version) -> str:
    return (
        f"{version[0]}."
        f"{version[1]}."
        f"{version[2]}"
    )


def parse_version(
    value: str,
) -> Version:
    parts = value.strip().split(".")

    if len(parts) != 3:
        raise ValueError(
            f"Invalid Solidity version: {value}"
        )

    return (
        int(parts[0]),
        int(parts[1]),
        int(parts[2]),
    )


def bump_patch(
    version: Version,
) -> Version:
    return (
        version[0],
        version[1],
        version[2] + 1,
    )


def next_major(
    version: Version,
) -> Version:
    return (
        version[0] + 1,
        0,
        0,
    )


def next_minor(
    version: Version,
) -> Version:
    return (
        version[0],
        version[1] + 1,
        0,
    )


def next_caret_upper(
    version: Version,
) -> Version:
    major, minor, patch = version

    if major > 0:
        return (
            major + 1,
            0,
            0,
        )

    if minor > 0:
        return (
            0,
            minor + 1,
            0,
        )

    return (
        0,
        0,
        patch + 1,
    )


def remove_comments(
    source: str,
) -> str:
    source = re.sub(
        r"//.*?$",
        "",
        source,
        flags=re.MULTILINE,
    )

    source = re.sub(
        r"/\*.*?\*/",
        "",
        source,
        flags=re.DOTALL,
    )

    return source


def extract_pragma(
    source: str,
) -> str | None:
    cleaned = remove_comments(source)

    match = PRAGMA_PATTERN.search(
        cleaned
    )

    if not match:
        return None

    return match.group(1).strip()


def parse_version_token(
    token: str,
) -> list[Constraint]:
    match = VERSION_TOKEN_PATTERN.match(
        token.strip()
    )

    if not match:
        raise ValueError(
            f"Unsupported Solidity pragma token: {token}"
        )

    operator = (
        match.group("operator")
        or ""
    )

    major = int(
        match.group("major")
    )

    minor_text = match.group("minor")
    patch_text = match.group("patch")

    minor = (
        None
        if minor_text is None
        or minor_text.lower() in {"x", "*"}
        else int(minor_text)
    )

    patch = (
        None
        if patch_text is None
        or patch_text.lower() in {"x", "*"}
        else int(patch_text)
    )

    base: Version = (
        major,
        minor or 0,
        patch or 0,
    )

    # Caret ranges.
    if operator == "^":
        return [
            (">=", base),
            (
                "<",
                next_caret_upper(base),
            ),
        ]

    # Tilde ranges.
    if operator == "~":
        if minor is None:
            upper = next_major(base)
        else:
            upper = next_minor(base)

        return [
            (">=", base),
            ("<", upper),
        ]

    # Comparison operators.
    if operator in {
        ">",
        ">=",
        "<",
        "<=",
        "=",
    }:
        return [
            (
                "=="
                if operator == "="
                else operator,
                base,
            )
        ]

    # No operator means exact version,
    # unless the user used a wildcard or partial version.
    if minor is None:
        return [
            (">=", base),
            (
                "<",
                next_major(base),
            ),
        ]

    if patch is None:
        return [
            (">=", base),
            (
                "<",
                next_minor(base),
            ),
        ]

    return [
        ("==", base)
    ]


def parse_pragma_expression(
    expression: str,
) -> list[list[Constraint]]:
    alternatives = expression.split(
        "||"
    )

    parsed_alternatives = []

    for alternative in alternatives:
        cleaned = (
            alternative
            .strip()
            .replace(",", " ")
        )

        tokens = re.findall(
            r"(?:\^|~|>=|<=|>|<|=)?"
            r"\s*v?"
            r"\d+"
            r"(?:\.(?:\d+|x|\*))?"
            r"(?:\.(?:\d+|x|\*))?",
            cleaned,
            flags=re.IGNORECASE,
        )

        compact_source = re.sub(
            r"\s+",
            "",
            cleaned,
        )

        compact_tokens = "".join(
            token.replace(" ", "")
            for token in tokens
        )

        if (
            not tokens
            or compact_tokens.lower()
            != compact_source.lower()
        ):
            raise ValueError(
                "Unsupported Solidity pragma expression: "
                f"{expression}"
            )

        constraints = []

        for token in tokens:
            constraints.extend(
                parse_version_token(token)
            )

        parsed_alternatives.append(
            constraints
        )

    return parsed_alternatives


def satisfies(
    version: Version,
    constraints: list[Constraint],
) -> bool:
    for operator, target in constraints:

        if operator == "==":
            if version != target:
                return False

        elif operator == ">":
            if not version > target:
                return False

        elif operator == ">=":
            if not version >= target:
                return False

        elif operator == "<":
            if not version < target:
                return False

        elif operator == "<=":
            if not version <= target:
                return False

        else:
            raise ValueError(
                f"Unsupported comparison operator: {operator}"
            )

    return True


def get_installed_versions() -> set[Version]:
    try:
        result = subprocess.run(
            [
                "solc-select",
                "versions",
            ],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return set()

    output = (
        result.stdout
        + "\n"
        + result.stderr
    )

    versions = re.findall(
        r"\b\d+\.\d+\.\d+\b",
        output,
    )

    return {
        parse_version(version)
        for version in versions
    }


def choose_fallback_version(
    alternatives: list[list[Constraint]],
) -> Version | None:
    candidates = []

    for constraints in alternatives:

        exact_versions = [
            target
            for operator, target
            in constraints
            if operator == "=="
        ]

        if exact_versions:
            candidates.extend(
                exact_versions
            )
            continue

        lower_bounds = [
            target
            for operator, target
            in constraints
            if operator in {">=", ">"}
        ]

        if lower_bounds:
            candidate = max(
                lower_bounds
            )

            has_strict_lower_bound = any(
                operator == ">"
                and target == candidate
                for operator, target
                in constraints
            )

            if has_strict_lower_bound:
                candidate = bump_patch(
                    candidate
                )

            candidates.append(
                candidate
            )

    for candidate in candidates:

        for constraints in alternatives:
            if satisfies(
                candidate,
                constraints,
            ):
                return candidate

    return None


def select_compiler_version(
    source_file: str | Path,
) -> str:
    source_path = Path(
        source_file
    ).resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"Solidity source not found: "
            f"{source_path}"
        )

    source = source_path.read_text(
        encoding="utf-8"
    )

    pragma = extract_pragma(
        source
    )

    if not pragma:
        print(
            "    No Solidity pragma found. "
            f"Using default solc {DEFAULT_SOLC_VERSION}."
        )

        return DEFAULT_SOLC_VERSION

    print(
        f"    Solidity pragma detected: "
        f"{pragma}"
    )

    alternatives = parse_pragma_expression(
        pragma
    )

    installed = get_installed_versions()

    default_version = parse_version(
        DEFAULT_SOLC_VERSION
    )

    installed.add(
        default_version
    )

    for constraints in alternatives:

        compatible = [
            version
            for version in installed
            if satisfies(
                version,
                constraints,
            )
        ]

        if compatible:
            selected = max(
                compatible
            )

            print(
                "    Compatible solc selected: "
                f"{format_version(selected)}"
            )

            return format_version(
                selected
            )

    fallback = choose_fallback_version(
        alternatives
    )

    if fallback is None:
        raise RuntimeError(
            "Could not determine a compatible "
            "Solidity compiler version for "
            f"pragma: {pragma}"
        )

    print(
        "    Compatible installed compiler "
        "not found."
    )

    print(
        "    Using pragma-compatible fallback: "
        f"{format_version(fallback)}"
    )

    return format_version(
        fallback
    )


def ensure_solc_version(
    version: str,
) -> None:
    parsed = parse_version(
        version
    )

    installed = get_installed_versions()

    if parsed in installed:
        return

    print(
        f"    Installing solc {version}..."
    )

    try:
        result = subprocess.run(
            [
                "solc-select",
                "install",
                version,
            ],
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"solc {version} installation timed out."
        ) from exc

    except FileNotFoundError as exc:
        raise RuntimeError(
            "solc-select is not installed."
        ) from exc

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to install Solidity compiler "
            f"{version}.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    print(
        f"    solc {version} installed."
    )


def get_solc_env_for_source(
    source_file: str | Path,
) -> dict[str, str]:
    version = select_compiler_version(
        source_file
    )

    ensure_solc_version(
        version
    )

    environment = os.environ.copy()

    # solc-select supports SOLC_VERSION as a
    # per-process override of the global compiler.
    environment["SOLC_VERSION"] = version

    print(
        f"    Using solc {version} for this analysis."
    )

    return environment