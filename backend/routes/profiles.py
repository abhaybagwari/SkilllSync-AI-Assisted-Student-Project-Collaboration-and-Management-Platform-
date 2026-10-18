
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from database.connection import get_connection

router = APIRouter(prefix="/profiles", tags=["Profiles"])


class ProfileRequest(BaseModel):
    college: str
    branch: str
    year_of_study: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=8)
    skills: list[str] = Field(min_length=1)
    interests: str = ""
    github_url: str = ""
    project_experience: str = ""
    document_metadata: list[dict] = Field(min_length=1)


@router.put("/{user_id}")
def save_profile(user_id: int, profile: ProfileRequest):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT User_ID, Role FROM User WHERE User_ID = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user["Role"] not in ("Team Member", "Team Leader"):
            raise HTTPException(
                status_code=403,
                detail="Only students and team leaders can save this profile"
            )

        cursor.execute(
            """
            INSERT INTO Student_Profile
            (User_ID, College, Branch, Year_Of_Study, Semester,
             Skills, Interests, Github_URL, Project_Experience,
             Document_Metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                College = VALUES(College),
                Branch = VALUES(Branch),
                Year_Of_Study = VALUES(Year_Of_Study),
                Semester = VALUES(Semester),
                Skills = VALUES(Skills),
                Interests = VALUES(Interests),
                Github_URL = VALUES(Github_URL),
                Project_Experience = VALUES(Project_Experience),
                Document_Metadata = VALUES(Document_Metadata)
            """,
            (
                user_id,
                profile.college.strip(),
                profile.branch,
                profile.year_of_study,
                profile.semester,
                json.dumps(profile.skills),
                profile.interests,
                profile.github_url,
                profile.project_experience,
                json.dumps(profile.document_metadata)
            )
        )

        connection.commit()

        return {
            "message": "Profile saved successfully",
            "user_id": user_id
        }

    except HTTPException:
        connection.rollback()
        raise
    except Exception:
        connection.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save profile to the database"
        )
    finally:
        cursor.close()
        connection.close()


@router.get("/{user_id}")
def get_profile(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                u.User_ID,
                u.Name,
                u.Email,
                u.Role,
                p.College,
                p.Branch,
                p.Year_Of_Study,
                p.Semester,
                p.Skills,
                p.Interests,
                p.Github_URL,
                p.Project_Experience,
                p.Document_Metadata,
                p.Updated_At
            FROM User u
            LEFT JOIN Student_Profile p ON p.User_ID = u.User_ID
            WHERE u.User_ID = %s
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        if isinstance(profile.get("Skills"), str):
            try:
                profile["Skills"] = json.loads(profile["Skills"])
            except json.JSONDecodeError:
                profile["Skills"] = []

        if isinstance(profile.get("Document_Metadata"), str):
            try:
                profile["Document_Metadata"] = json.loads(
                    profile["Document_Metadata"]
                )
            except json.JSONDecodeError:
                profile["Document_Metadata"] = []

        return profile

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve profile from the database"
        )
    finally:
        cursor.close()
        connection.close()
