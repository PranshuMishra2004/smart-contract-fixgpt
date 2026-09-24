import os

from dotenv import load_dotenv
from google import genai

from analyzer.ai_prompt_builder import build_fix_prompt
from analyzer.ai_prompt_builder import build_repair_prompt
from analyzer.ai_response_model import AIFixResponse
from analyzer.finding_model import SecurityFinding


load_dotenv()


def get_client() -> genai.Client:
    """
    Create and return a Gemini API client.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Add it to the .env file."
        )

    return genai.Client(
        api_key=api_key
    )


def request_ai(
    prompt: str,
) -> AIFixResponse:
    """
    Send a prompt to Gemini and validate the
    structured response.
    """

    client = get_client()

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    response = client.interactions.create(
        model=model,
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": (
                AIFixResponse.model_json_schema()
            ),
        },
        timeout=180,
    )

    return AIFixResponse.model_validate_json(
        response.output_text
    )


def analyze_with_ai(
    finding: SecurityFinding,
) -> AIFixResponse:
    """
    Generate an initial remediation.
    """

    print(
        "  → Sending finding to Gemini..."
    )

    result = request_ai(
        build_fix_prompt(finding)
    )

    print(
        "  → Gemini response received."
    )

    return result


def repair_with_ai(
    finding: SecurityFinding,
    previous_code: str,
    compiler_error: str,
) -> AIFixResponse:
    """
    Ask Gemini to repair a Solidity fix that failed
    compilation.
    """

    print(
        "  → Sending compiler error back to Gemini..."
    )

    prompt = build_repair_prompt(
        finding=finding,
        previous_code=previous_code,
        compiler_error=compiler_error,
    )

    result = request_ai(prompt)

    print(
        "  → Gemini repaired the generated fix."
    )

    return result