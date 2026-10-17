
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from database.connection import get_connection

router = APIRouter(prefix="/mentor", tags=["Mentor"])


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback_text: str = Field(min_length=1, max_length=10000)


def verify_mentor(cursor, mentor_id):
    cursor.execute(
        "SELECT User_ID FROM User WHERE User_ID = %s AND Role = 'Mentor'",
        (mentor_id,)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mentor not found")


def verify_assignment(cursor, mentor_id, project_id):
    cursor.execute(
        """
        SELECT Project_ID
        FROM Mentor_Project
        WHERE Mentor_ID = %s AND Project_ID = %s
        """,
        (mentor_id, project_id)
    )
    if not cursor.fetchone():
        raise HTTPException(
            status_code=403,
            detail="This project is not assigned to this mentor"
        )


@router.get("/{mentor_id}/profile")
def get_profile(mentor_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        verify_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT User_ID, Name, Email, Role
            FROM User
            WHERE User_ID = %s
            """,
            (mentor_id,)
        )
        return {"profile": cursor.fetchone()}
    finally:
        cursor.close()
        connection.close()


@router.get("/{mentor_id}/projects")
def get_projects(mentor_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        verify_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT
                p.Project_ID,
                p.Project_Name,
                p.Project_Description,
                p.Skill_Required,
                p.Submission_Date,
                u.Name AS Leader_Name,
                (
                    SELECT COUNT(*)
                    FROM Project_Members pm
                    WHERE pm.Project_ID = p.Project_ID
                    AND pm.Status = 'Accepted'
                ) AS Total_Members,
                (
                    SELECT COUNT(*)
                    FROM Mentor_Interaction mi
                    WHERE mi.Project_ID = p.Project_ID
                    AND mi.Mentor_ID = %s
                    AND mi.Status = 'Completed'
                ) AS Completed_Interactions,
                (
                    SELECT COUNT(*)
                    FROM Mentor_Interaction mi
                    WHERE mi.Project_ID = p.Project_ID
                    AND mi.Mentor_ID = %s
                    AND mi.Status = 'Pending'
                ) AS Pending_Interactions
            FROM Mentor_Project mp
            JOIN Project_Details p ON p.Project_ID = mp.Project_ID
            JOIN User u ON u.User_ID = p.User_ID
            WHERE mp.Mentor_ID = %s
            ORDER BY mp.Assigned_Date DESC, p.Project_ID DESC
            """,
            (mentor_id, mentor_id, mentor_id)
        )
        return {"projects": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@router.get("/{mentor_id}/projects/{project_id}/members")
def get_members(mentor_id: int, project_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        verify_mentor(cursor, mentor_id)
        verify_assignment(cursor, mentor_id, project_id)
        cursor.execute(
            """
            SELECT u.User_ID, u.Name, u.Email, pm.Status
            FROM Project_Members pm
            JOIN User u ON u.User_ID = pm.User_ID
            WHERE pm.Project_ID = %s AND pm.Status = 'Accepted'
            ORDER BY u.Name
            """,
            (project_id,)
        )
        return {"members": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@router.get("/{mentor_id}/projects/{project_id}/feedback")
def get_feedback(mentor_id: int, project_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        verify_mentor(cursor, mentor_id)
        verify_assignment(cursor, mentor_id, project_id)
        cursor.execute(
            """
            SELECT Feedback_ID, Rating, Feedback_Text, Feedback_Date
            FROM Project_Feedback
            WHERE Mentor_ID = %s AND Project_ID = %s
            ORDER BY Feedback_Date DESC
            """,
            (mentor_id, project_id)
        )
        return {"feedback": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@router.post("/{mentor_id}/projects/{project_id}/feedback")
def save_feedback(
    mentor_id: int,
    project_id: int,
    request: FeedbackRequest
):
    feedback_text = request.feedback_text.strip()
    if not feedback_text:
        raise HTTPException(
            status_code=400,
            detail="Feedback cannot be empty"
        )

    connection = get_connection()
    cursor = connection.cursor()
    try:
        verify_mentor(cursor, mentor_id)
        verify_assignment(cursor, mentor_id, project_id)
        cursor.execute(
            """
            INSERT INTO Project_Feedback
                (Mentor_ID, Project_ID, Rating, Feedback_Text)
            VALUES (%s, %s, %s, %s)
            """,
            (mentor_id, project_id, request.rating, feedback_text)
        )
        connection.commit()
        return {
            "message": "Feedback saved successfully",
            "feedback_id": cursor.lastrowid
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
