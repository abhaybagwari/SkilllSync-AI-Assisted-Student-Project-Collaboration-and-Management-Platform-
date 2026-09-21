from fastapi import APIRouter
from pydantic import BaseModel
from database.connection import get_connection

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    project_name: str
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
                Members_Required,
                Skill_Required,
                Submission_Date,
                User_ID
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                project.project_name,
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