
import os
from google import genai


MODEL_NAME = "gemini-3.8-flash"


def ask_gemini(question, project_context=""):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are SkillSync AI, an assistant for student project collaboration.

    Help students with project planning, programming concepts,
    task guidance, skill improvement and project progress.

    Use the following project information when relevant:

    {project_context}

    Student question:
    {question}

    Give a clear, practical and beginner-friendly answer.
    Do not invent project information that is not provided.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text
