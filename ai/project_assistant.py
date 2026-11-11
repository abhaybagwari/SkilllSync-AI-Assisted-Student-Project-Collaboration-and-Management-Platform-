"""Gemini helper used by backend/routes/ai_assistant.py"""

import os
import time

from google import genai
from google.genai import types


SYSTEM_INSTRUCTION = (
    "You are SkillSync AI, a polite and knowledgeable project mentor for "
    "engineering students; faculty members may also use you. "
    "Use a clear, professional tone with at most one or two relevant emojis. "
    "Reply in the same language as the student's question: English by default, "
    "Hinglish if the question is in Hinglish, and the regional language if the "
    "question is in one. "
    "Answer directly and completely using the project data provided. "
    "Never ask the user to log in or do any setup. "
    "Keep answers concise and use bullet points for lists."
)

# Tried in this order; the next one is used if a model is unavailable.
PREFERRED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

REQUEST_TIMEOUT_MS = 15000      # give up on a slow model after 15 seconds
FAILED_MODEL_COOLDOWN = 120     # skip a model for 2 minutes after it fails

_client = None
_client_key = None
_working_model = None      # last model that answered: tried first next time
_failed_until = {}         # model -> time until which it is skipped


def _get_client():
    global _client, _client_key

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key or "PASTE" in api_key.upper() or len(api_key) < 20:
        raise RuntimeError(
            "GEMINI_API_KEY is missing or is not a real key. "
            "Set it in the same terminal that runs the backend."
        )

    if _client is None or api_key != _client_key:
        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
        _client_key = api_key

    return _client


def _discover_models(client, already_tried):
    """Ask Google which flash models this key can use (names change often)."""
    found = []

    try:
        for model in client.models.list():
            name = getattr(model, "name", "") or ""
            short = name.replace("models/", "")
            actions = getattr(model, "supported_actions", None) or []

            if "flash" not in short or short in already_tried:
                continue

            if actions and "generateContent" not in actions:
                continue

            found.append(short)
    except Exception as error:
        print(f"[SkillSync AI] could not list models: {error}", flush=True)

    # Prefer regular flash models over lite / preview / image / audio ones.
    def rank(name):
        return (
            any(word in name for word in ("lite", "preview", "image", "tts", "live", "audio", "thinking")),
            name,
        )

    return sorted(found, key=rank)[:6]


def _generate(client, model, contents):
    def call(config):
        response = client.models.generate_content(
            model=model, contents=contents, config=config
        )
        return (response.text or "").strip()

    fast = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.4,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    try:
        return call(fast)
    except Exception as error:
        # Some models do not allow turning thinking off: retry normally.
        if "thinking" in str(error).lower():
            return call(
                types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.4,
                )
            )

        raise


def ask_gemini(question, project_context=""):
    client = _get_client()

    contents = (
        "Project data from the database (may be empty):\n"
        f"{project_context}\n\n"
        f"Student question:\n{question}"
    )

    models = []
    custom_model = os.getenv("GEMINI_MODEL")

    if custom_model:
        models.append(custom_model)

    models += [m for m in PREFERRED_MODELS if m not in models]

    global _working_model

    if _working_model in models:
        models.remove(_working_model)
        models.insert(0, _working_model)

    last_error = None
    tried = []

    for stage in range(2):
        now = time.time()
        # skip models that failed a moment ago (unless nothing else is left)
        usable = [m for m in models if _failed_until.get(m, 0) <= now] or models

        for model in usable:
            tried.append(model)

            try:
                text = _generate(client, model, contents)

                if text:
                    _working_model = model
                    return text

                last_error = RuntimeError(f"{model} returned an empty response")

            except Exception as error:
                print(f"[SkillSync AI] model {model} failed: {error}", flush=True)
                _failed_until[model] = time.time() + FAILED_MODEL_COOLDOWN
                last_error = error

        if stage == 0:
            models = _discover_models(client, set(tried))

            if not models:
                break

            print(f"[SkillSync AI] trying discovered models: {models}", flush=True)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


if __name__ == "__main__":
    print(ask_gemini("Explain SkillSync in two simple lines.", "No project data."))