
"""Gemini helper used by the SkillSync project assistant."""

import os
import re
import time

from google import genai
from google.genai import types


SYSTEM_INSTRUCTION = (
    "You are SkillSync AI, a knowledgeable project mentor for engineering "
    "students and faculty members. "
    "Reply in the same language as the user's question: English by default, "
    "Hinglish when the user writes in Hinglish, and the relevant regional "
    "language when appropriate. "
    "Use the supplied project data when answering questions about the user's "
    "projects. Do not invent project details or claim access to data that "
    "was not supplied. "
    "Answer clearly and directly. Keep answers concise and use bullet points "
    "when useful."
)

# Use text-generation models only.
DEFAULT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

REQUEST_TIMEOUT_MS = 60000
MAX_RETRIES = 5

_client = None
_client_key = None
_working_model = None


def _get_client():
    global _client, _client_key

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key or "PASTE" in api_key.upper() or len(api_key) < 20:
        raise RuntimeError(
            "Gemini API key is missing or invalid. "
            "Set GEMINI_API_KEY in the terminal running the backend."
        )

    if _client is None or api_key != _client_key:
        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS
            ),
        )
        _client_key = api_key

    return _client


def _get_error_code(error):
    """Extract an HTTP/API status code from an SDK error."""
    match = re.search(r"\b(400|401|403|404|408|429|500|502|503|504)\b", str(error))
    return int(match.group(1)) if match else None


def _generate(client, model, contents):
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        max_output_tokens=1024,
    )

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            answer = (response.text or "").strip()

            if answer:
                return answer

            raise RuntimeError(
                f"{model} returned an empty response."
            )

        except Exception as error:
            last_error = error
            status_code = _get_error_code(error)

            # Retry only temporary server/network errors.
            if status_code not in (408, 500, 502, 503, 504):
                raise

            if attempt < MAX_RETRIES - 1:
                wait_seconds = 2 ** attempt
                print(
                    f"[SkillSync AI] {model} temporarily failed "
                    f"({status_code}). Retrying in {wait_seconds}s.",
                    flush=True,
                )
                time.sleep(wait_seconds)

    raise last_error


def ask_gemini(question, project_context=""):
    global _working_model

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    client = _get_client()

    contents = (
        "Project data from the database (may be empty):\n"
        f"{project_context or 'No project data available.'}\n\n"
        "Student question:\n"
        f"{question.strip()}"
    )

    custom_model = os.getenv("GEMINI_MODEL", "").strip()

    models = []
    if custom_model:
        models.append(custom_model)

    models.extend(DEFAULT_MODELS)

    # Remove duplicates while preserving order.
    models = list(dict.fromkeys(models))

    # Try the last successful model first next time.
    if _working_model in models:
        models.remove(_working_model)
        models.insert(0, _working_model)

    errors = []

    for model in models:
        try:
            print(
                f"[SkillSync AI] trying model: {model}",
                flush=True,
            )

            answer = _generate(client, model, contents)

            _working_model = model

            print(
                f"[SkillSync AI] response generated using {model}",
                flush=True,
            )

            return answer

        except Exception as error:
            errors.append(f"{model}: {error}")

            print(
                f"[SkillSync AI] model {model} failed: {error}",
                flush=True,
            )

    raise RuntimeError(
        "All configured Gemini text models failed. "
        + " | ".join(errors)
    )


if __name__ == "__main__":
    print(
        ask_gemini(
            "Explain SkillSync in two simple lines.",
            "No project data.",
        )
    )
