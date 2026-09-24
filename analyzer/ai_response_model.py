from pydantic import BaseModel, Field


class AIFixResponse(BaseModel):
    vulnerability: str = Field(
        description="Name of the detected vulnerability."
    )

    severity: str = Field(
        description="Severity of the vulnerability."
    )

    explanation: str = Field(
        description="Clear explanation of the vulnerability."
    )

    root_cause: str = Field(
        description="Specific root cause in the provided Solidity code."
    )

    recommendation: str = Field(
        description="Recommended remediation."
    )

    fixed_code: str = Field(
        description="Corrected Solidity code for the affected section."
    )

    verification_notes: str = Field(
        description="Checks that should be performed to verify the fix."
    )