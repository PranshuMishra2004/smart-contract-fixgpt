from analyzer.finding_model import SecurityFinding


def build_fix_prompt(
    finding: SecurityFinding,
) -> str:
    """
    Build the initial remediation prompt.
    """

    prompt = (
        "You are a smart contract security assistant.\n\n"

        "Analyze the following Solidity security finding.\n\n"

        "Security Finding:\n"
        f"- Vulnerability: {finding.category}\n"
        f"- Severity: {finding.severity}\n"
        f"- Confidence: {finding.confidence}\n"
        f"- Detector: {finding.check}\n"
        f"- Function: {finding.function}\n"
        f"- File: {finding.file}\n"
        f"- Affected lines: "
        f"{finding.start_line}-{finding.end_line}\n\n"

        "Description:\n"
        f"{finding.description}\n\n"

        "Relevant Solidity source:\n"
        "```solidity\n"
        f"{finding.source_code}\n"
        "```\n\n"

        "Your task:\n"
        "1. Explain the vulnerability briefly.\n"
        "2. Identify the root cause.\n"
        "3. Give the safest practical remediation.\n"
        "4. Provide corrected Solidity code for the affected section.\n"
        "5. Give concise verification steps.\n\n"

        "Important rules:\n"
        "- Do not invent vulnerabilities.\n"
        "- Preserve intended behavior.\n"
        "- Do not claim the fix is secure until independently verified.\n"
        "- Keep the response concise.\n"
        "- Return only valid JSON matching the AIFixResponse schema."
    )

    return prompt


def build_repair_prompt(
    finding: SecurityFinding,
    previous_code: str,
    compiler_error: str,
) -> str:
    """
    Build a repair prompt after the previous AI-generated
    Solidity failed compilation.
    """

    prompt = (
        "You are repairing a Solidity security fix that "
        "failed compilation.\n\n"

        "Original Security Finding:\n"
        f"- Vulnerability: {finding.category}\n"
        f"- Severity: {finding.severity}\n"
        f"- Detector: {finding.check}\n"
        f"- Function: {finding.function}\n"
        f"- File: {finding.file}\n\n"

        "Original Source Code:\n"
        "```solidity\n"
        f"{finding.source_code}\n"
        "```\n\n"

        "Previous AI-generated fix:\n"
        "```solidity\n"
        f"{previous_code}\n"
        "```\n\n"

        "Compiler error from that fix:\n"
        "```text\n"
        f"{compiler_error}\n"
        "```\n\n"

        "Your task:\n"
        "1. Correct the compilation error.\n"
        "2. Preserve the intended security remediation.\n"
        "3. Return the corrected Solidity code for the affected section.\n"
        "4. Keep the response concise.\n\n"

        "Important rules:\n"
        "- Do not introduce unrelated changes.\n"
        "- Do not invent new vulnerabilities.\n"
        "- Return only valid JSON matching the AIFixResponse schema."
    )

    return prompt