
import sys
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2]))

from ai.project_assistant import ask_gemini
from database.connection import get_connection
from backend.utils.auth_dependency import get_current_user


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ai/assistant",
    tags=["AI Assistant"]
)


class AssistantRequest(BaseModel):
    question: str


def get_student_projects(user_id, role):

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        if role == "Team Member":

            query = """
                SELECT
                    p.Project_Name,
                    p.Project_Description,
                    p.Skill_Required,
                    p.Submission_Date,
                    pm.Status
                FROM Project_Members pm
                JOIN Project_Details p
                    ON pm.Project_ID = p.Project_ID
                WHERE pm.User_ID = %s
            """

        elif role == "Team Leader":

            query = """
                SELECT
                    Project_Name,
                    Project_Description,
                    Skill_Required,
                    Submission_Date
                FROM Project_Details
                WHERE User_ID = %s
            """

        elif role == "Mentor":

            query = """
                SELECT
                    p.Project_Name,
                    p.Project_Description,
                    p.Skill_Required,
                    p.Submission_Date
                FROM Mentor_Project mp
                JOIN Project_Details p
                    ON mp.Project_ID = p.Project_ID
                WHERE mp.Mentor_ID = %s
            """

        else:
            return []

        cursor.execute(query, (user_id,))

        return cursor.fetchall()

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


@router.post("/chat")
def assistant_chat(
    request: AssistantRequest,
    current_user: dict = Depends(get_current_user)
):

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    user_id = current_user["user_id"]
    role = current_user["role"]

    projects = []

    project_context = (
        "Project information is currently unavailable."
    )

    # STEP 1: Fetch student project information

    try:

        projects = get_student_projects(
            user_id,
            role
        )

        if projects:

            project_context = str(projects)

        else:

            project_context = (
                "No projects are currently associated "
                "with this user."
            )

    except Exception:

        logger.exception(
            "Failed to fetch student project information"
        )

    # STEP 2: Generate AI response

    try:

        answer = ask_gemini(
            request.question,
            project_context
        )

        if not answer or not answer.strip():

            raise RuntimeError(
                "AI returned an empty response"
            )

        return {
            "success": True,
            "answer": answer.strip(),
            "projects_found": len(projects)
        }

    except Exception as error:

        logger.exception(
            "SkillSync AI response generation failed"
        )

        raise HTTPException(
            status_code=502,
            detail="AI response generation failed. Please try again."
        ) from error
