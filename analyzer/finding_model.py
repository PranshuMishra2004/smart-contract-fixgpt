from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SecurityFinding:
    check: str
    category: str
    severity: str
    confidence: str
    description: str
    function: str | None
    file: str | None
    start_line: int | None
    end_line: int | None
    source_code: str

    # Human-readable remediation guidance for the
    # detected vulnerability.
    resolution: str = ""

    source: str = "Slither"

    def to_dict(self) -> dict:
        """
        Convert the security finding into a normal
        dictionary for JSON/report generation.
        """

        return asdict(self)