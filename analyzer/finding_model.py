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
    source: str = "Slither"

    def to_dict(self) -> dict:
        return asdict(self)