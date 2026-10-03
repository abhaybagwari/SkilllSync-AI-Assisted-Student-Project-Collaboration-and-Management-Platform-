from fastapi import APIRouter, HTTPException
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


class JoinProjectRequest(BaseModel):
    user_id: int


@router.post("/")
def create_project(project: ProjectCreate):

    if project.members_required < 1:
        raise HTTPException(
            status_code=400,
            detail="Members required must be at least 1"
        )

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
                project.project_name.strip(),
                project.project_description.strip(),
                project.members_required,
                project.skill_required.strip(),
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


@router.get("/")
def get_all_projects():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                p.Project_ID,
                p.Project_Name,
                p.Project_Description,
                p.Members_Required,
                p.Skill_Required,
                p.Submission_Date,
                p.User_ID AS Leader_ID,
                u.Name AS Leader_Name
            FROM Project_Details p
            JOIN User u ON p.User_ID = u.User_ID
            ORDER BY p.Project_ID DESC
            """
        )

        return {"projects": cursor.fetchall()}

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

        return {"projects": cursor.fetchall()}

    finally:
        cursor.close()
        connection.close()


@router.post("/{project_id}/apply")
def apply_to_project(project_id: int, request: JoinProjectRequest):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT Project_ID, User_ID, Members_Required
            FROM Project_Details
            WHERE Project_ID = %s
            """,
            (project_id,)
        )

        project = cursor.fetchone()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        if project["User_ID"] == request.user_id:
            raise HTTPException(
                status_code=400,
                detail="Project leader cannot apply to their own project"
            )

        cursor.execute(
            """
            SELECT Member_ID, Status
            FROM Project_Members
            WHERE Project_ID = %s AND User_ID = %s
            """,
            (project_id, request.user_id)
        )

        existing = cursor.fetchone()

        if existing:
            if existing["Status"] == "Rejected":
                cursor.execute(
                    """
                    UPDATE Project_Members
                    SET Status = 'Pending'
                    WHERE Member_ID = %s
                    """,
                    (existing["Member_ID"],)
                )

                connection.commit()

                return {
                    "message": "Application submitted again"
                }

            raise HTTPException(
                status_code=400,
                detail=f"You already have a {existing['Status'].lower()} application for this project"
            )

        cursor.execute(
            """
            SELECT COUNT(*) AS accepted_count
            FROM Project_Members
            WHERE Project_ID = %s AND Status = 'Accepted'
            """,
            (project_id,)
        )

        accepted_count = cursor.fetchone()["accepted_count"]

        if accepted_count >= project["Members_Required"]:
            raise HTTPException(
                status_code=400,
                detail="This project is already full"
            )

        cursor.execute(
            """
            INSERT INTO Project_Members
            (Project_ID, User_ID, Status)
            VALUES (%s, %s, 'Pending')
            """,
            (project_id, request.user_id)
        )

        connection.commit()

        return {
            "message": "Application submitted successfully"
        }

    finally:
        cursor.close()
        connection.close()


@router.get("/member/{user_id}")
def get_member_projects(user_id: int):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                p.Project_ID,
                p.Project_Name,
                p.Project_Description,
                p.Members_Required,
                p.Skill_Required,
                p.Submission_Date,
                pm.Status,
                u.Name AS Leader_Name
            FROM Project_Members pm
            JOIN Project_Details p
                ON pm.Project_ID = p.Project_ID
            JOIN User u
                ON p.User_ID = u.User_ID
            WHERE pm.User_ID = %s
            ORDER BY pm.Member_ID DESC
            """,
            (user_id,)
        )

        return {
            "projects": cursor.fetchall()
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
                u.Name,
                u.Email
            FROM Project_Members pm
            JOIN User u
                ON pm.User_ID = u.User_ID
            WHERE pm.Project_ID = %s
            ORDER BY pm.Member_ID DESC
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
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                pm.Project_ID,
                p.Members_Required
            FROM Project_Members pm
            JOIN Project_Details p
                ON pm.Project_ID = p.Project_ID
            WHERE pm.Member_ID = %s
            AND pm.Status = 'Pending'
            """,
            (member_id,)
        )

        application = cursor.fetchone()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Pending application not found"
            )

        cursor.execute(
            """
            SELECT COUNT(*) AS accepted_count
            FROM Project_Members
            WHERE Project_ID = %s
            AND Status = 'Accepted'
            """,
            (application["Project_ID"],)
        )

        accepted_count = cursor.fetchone()["accepted_count"]

        if accepted_count >= application["Members_Required"]:
            raise HTTPException(
                status_code=400,
                detail="Project team is already full"
            )

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
            AND Status = 'Pending'
            """,
            (member_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Pending application not found"
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

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Member not found"
            )

        connection.commit()

        return {
            "message": "Member removed successfully"
        }

    finally:
        cursor.close()
        connection.close()

