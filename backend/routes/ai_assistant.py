
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[2]))

from ai.project_assistant import ask_gemini
from database.connection import get_connection
from backend.utils.auth_dependency import get_current_user


router = APIRouter(
    prefix="/ai/assistant",
    tags=["AI Assistant"]
)


class AssistantRequest(BaseModel):
    question: str


def get_student_projects(user_id, role):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
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
        cursor.close()
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

    try:
        projects = get_student_projects(
            current_user["user_id"],
            current_user["role"]
        )

        if projects:
            project_context = str(projects)
        else:
            project_context = (
                "No projects are currently associated "
                "with this user."
            )

        answer = ask_gemini(
            request.question,
            project_context
        )

        return {
            "success": True,
            "answer": answer,
            "projects_found": len(projects)
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to process AI assistant request"
        )
