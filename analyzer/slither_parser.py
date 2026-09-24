import json
from pathlib import Path

from analyzer.finding_model import SecurityFinding
from analyzer.source_reader import read_source_lines
from analyzer.vulnerability_classifier import classify_finding


def parse_slither_report(report_path: str) -> list[dict]:
    """
    Read a Slither JSON report and convert detector results
    into a simpler structure for FixGPT.
    """

    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Report not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    if not report.get("success"):
        raise RuntimeError(
            f"Slither report contains an error: "
            f"{report.get('error')}"
        )

    detectors = (
        report
        .get("results", {})
        .get("detectors", [])
    )

    findings = []

    for detector in detectors:
        finding = {
            "check": detector.get("check"),
            "impact": detector.get("impact"),
            "confidence": detector.get("confidence"),
            "description": detector.get("description"),
            "elements": [],
        }

        for element in detector.get("elements", []):
            source_mapping = element.get(
                "source_mapping",
                {},
            )

            finding["elements"].append(
                {
                    "type": element.get("type"),
                    "name": element.get("name"),
                    "file": source_mapping.get(
                        "filename_relative"
                    ),
                    "lines": source_mapping.get(
                        "lines",
                        [],
                    ),
                }
            )

        findings.append(finding)

    return findings


def resolve_source_file(
    file_name: str,
    source_root: str = "",
) -> Path:
    """
    Find the Solidity source file referenced by Slither.

    Supports:
    1. Uploaded files referenced from the project root.
    2. Foundry source files inside contracts/.
    3. Explicit source_root paths.
    """

    candidates = []

    if source_root:
        candidates.append(
            Path(source_root) / file_name
        )

    candidates.append(Path(file_name))

    candidates.append(
        Path("contracts") / file_name
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"Could not locate Solidity source file: "
        f"{file_name}"
    )


def analyze_report(
    report_file: str,
    source_root: str = "",
) -> list[SecurityFinding]:
    """
    Parse a Slither report and convert every detector
    finding into a SecurityFinding object.
    """

    findings = parse_slither_report(
        report_file
    )

    security_findings = []

    for finding in findings:
        classified = classify_finding(
            finding
        )

        function_name = None
        file_name = None
        start_line = None
        end_line = None
        source_code = ""

        for element in classified["elements"]:

            if element["type"] == "function":

                function_name = element["name"]
                file_name = element["file"]

                if element["lines"]:

                    start_line = min(
                        element["lines"]
                    )

                    end_line = max(
                        element["lines"]
                    )

                    source_path = resolve_source_file(
                        file_name,
                        source_root,
                    )

                    source_code = read_source_lines(
                        str(source_path),
                        start_line,
                        end_line,
                    )

                break

        security_finding = SecurityFinding(
            check=classified["check"],
            category=classified["category"],
            severity=classified["severity"],
            confidence=classified["confidence"],
            description=classified["description"],
            function=function_name,
            file=file_name,
            start_line=start_line,
            end_line=end_line,
            source_code=source_code,
        )

        security_findings.append(
            security_finding
        )

    return security_findings


if __name__ == "__main__":

    report_file = (
        "reports/vulnerable-bank.json"
    )

    security_findings = analyze_report(
        report_file
    )

    print(
        f"Found {len(security_findings)} "
        f"security findings:\n"
    )

    for index, finding in enumerate(
        security_findings,
        start=1,
    ):

        print(
            f"Finding #{index}"
        )

        print(
            finding.to_dict()
        )

        print("-" * 60)