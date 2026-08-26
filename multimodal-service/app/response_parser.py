"""Parsing and schema validation for multimodal model responses."""

import json
import re

from pydantic import ValidationError

from schemas import AnalyzeResponse


def parse_multimodal_response(response_text: str) -> dict:
    """Parse plain or fenced JSON and enforce the public response contract."""
    if not isinstance(response_text, str) or not response_text.strip():
        raise ValueError("Multimodal response is empty")

    cleaned = response_text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Multimodal response is not valid JSON: {error.msg}"
        ) from error

    try:
        validated = AnalyzeResponse.model_validate(result)
    except ValidationError as error:
        missing = [
            ".".join(str(part) for part in item["loc"])
            for item in error.errors()
            if item["type"] == "missing"
        ]
        if missing:
            raise ValueError(
                "Multimodal response is missing required fields: " + ", ".join(missing)
            ) from error
        raise ValueError(
            f"Multimodal response does not match the required schema: {error}"
        ) from error

    return validated.model_dump()
