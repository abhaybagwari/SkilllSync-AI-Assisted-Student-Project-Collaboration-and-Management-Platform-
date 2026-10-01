from fastapi import APIRouter
from pydantic import BaseModel
from database.connection import get_connection

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    project_name: str
    project_description: str
    members_required: int
    skill_required: str
    submission_date: str
    user_id: int


@router.post("/")
def create_project(project: ProjectCreate):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO Project_Details
            (
                Project_Name,
                Project_Description,
                Members_Required,
                Skill_Required,
                Submission_Date,
                User_ID
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                project.project_name,
                project.project_description,
                project.members_required,
                project.skill_required,
                project.submission_date,
                project.user_id
            )
        )

        connection.commit()

        return {
            "message": "Project created successfully",
            "project_id": cursor.lastrowid
        }

    finally:
        cursor.close()
        connection.close()


@router.get("/user/{user_id}")
def get_projects(user_id: int):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                Project_ID,
                Project_Name,
                Project_Description,
                Members_Required,
                Skill_Required,
                Submission_Date
            FROM Project_Details
            WHERE User_ID = %s
            ORDER BY Project_ID DESC
            """,
            (user_id,)
        )

        projects = cursor.fetchall()

        return {
            "projects": projects
        }

    finally:
        cursor.close()
        connection.close()


@router.get("/{project_id}/members")
def get_project_members(project_id: int):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                pm.Member_ID,
                pm.Project_ID,
                pm.User_ID,
                pm.Status,
                u.Email
            FROM Project_Members pm
            JOIN user u
                ON pm.User_ID = u.User_ID
            WHERE pm.Project_ID = %s
            """,
            (project_id,)
        )

        rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT Members_Required
            FROM Project_Details
            WHERE Project_ID = %s
            """,
            (project_id,)
        )

        project = cursor.fetchone()

        members = [
            row for row in rows
            if row["Status"] == "Accepted"
        ]

        applications = [
            row for row in rows
            if row["Status"] == "Pending"
        ]

        return {
            "members": members,
            "applications": applications,
            "members_required": (
                project["Members_Required"]
                if project
                else 0
            )
        }

    finally:
        cursor.close()
        connection.close()


@router.put("/members/{member_id}/accept")
def accept_member(member_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE Project_Members
            SET Status = 'Accepted'
            WHERE Member_ID = %s
            """,
            (member_id,)
        )

        connection.commit()

        return {
            "message": "Member accepted successfully"
        }

    finally:
        cursor.close()
        connection.close()


@router.put("/members/{member_id}/reject")
def reject_member(member_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE Project_Members
            SET Status = 'Rejected'
            WHERE Member_ID = %s
            """,
            (member_id,)
        )

        connection.commit()

        return {
            "message": "Application rejected successfully"
        }

    finally:
        cursor.close()
        connection.close()


@router.delete("/members/{member_id}")
def remove_member(member_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM Project_Members
            WHERE Member_ID = %s
            """,
            (member_id,)
        )

        connection.commit()

        return {
            "message": "Member removed successfully"
        }

    finally:
        cursor.close()
        connection.close()