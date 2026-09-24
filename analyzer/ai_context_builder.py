from analyzer.finding_model import SecurityFinding


def build_ai_context(finding: SecurityFinding) -> str:
    """
    Convert a SecurityFinding into structured context
    that can later be supplied to an AI model.
    """

    return f"""
Smart Contract Security Finding

Vulnerability:
{finding.category}

Severity:
{finding.severity}

Confidence:
{finding.confidence}

Detector:
{finding.check}

Function:
{finding.function}

File:
{finding.file}

Affected Lines:
{finding.start_line}-{finding.end_line}

Description:
{finding.description}

Source Code:
{finding.source_code}
""".strip()