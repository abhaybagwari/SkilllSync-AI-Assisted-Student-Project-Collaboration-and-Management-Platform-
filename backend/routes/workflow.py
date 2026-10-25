from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.connection import get_connection

router = APIRouter(prefix="/workflow", tags=["Workflow"])

EDIT_WINDOW_DAYS = 7


class ReviewRequest(BaseModel):
    reviewer_id: int
    reviewee_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)


def _check_mentor(cursor, mentor_id):
    cursor.execute(
        "SELECT User_ID FROM User WHERE User_ID = %s AND Role = 'Mentor'",
        (mentor_id,),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mentor not found")


def _team_ids(cursor, project_id):
    cursor.execute(
        """
        SELECT p.User_ID AS User_ID
        FROM Project_Details p
        WHERE p.Project_ID = %s
        UNION
        SELECT pm.User_ID
        FROM Project_Members pm
        WHERE pm.Project_ID = %s AND pm.Status = 'Accepted'
        """,
        (project_id, project_id),
    )
    return {row["User_ID"] for row in cursor.fetchall()}


def _completed_project(cursor, project_id):
    cursor.execute(
        """
        SELECT Project_ID, Project_Name, Project_Status
        FROM Project_Details
        WHERE Project_ID = %s
        """,
        (project_id,),
    )
    project = cursor.fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project["Project_Status"] != "Completed":
        raise HTTPException(
            status_code=400,
            detail="Reviews open only after the project is completed",
        )
    return project


@router.get("/mentors/{mentor_id}/available-projects")
def available_projects(mentor_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        _check_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT p.Project_ID, p.Project_Name, p.Project_Description,
                   p.Skill_Required, p.Submission_Date,
                   u.Name AS Leader_Name
            FROM Project_Details p
            JOIN User u ON u.User_ID = p.User_ID
            WHERE p.Project_Status <> 'Completed'
              AND NOT EXISTS (
                  SELECT 1 FROM Mentor_Project mp
                  WHERE mp.Project_ID = p.Project_ID
              )
            ORDER BY p.Project_ID DESC
            """
        )
        return {"projects": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@router.post("/mentors/{mentor_id}/projects/{project_id}/take")
def take_project(mentor_id: int, project_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        _check_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT Project_Status
            FROM Project_Details
            WHERE Project_ID = %s
            FOR UPDATE
            """,
            (project_id,),
        )
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["Project_Status"] == "Completed":
            raise HTTPException(
                status_code=400, detail="This project is already completed"
            )

        cursor.execute(
            "SELECT 1 FROM Mentor_Project WHERE Project_ID = %s",
            (project_id,),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409, detail="This project already has a mentor"
            )

        cursor.execute(
            "INSERT INTO Mentor_Project (Mentor_ID, Project_ID) VALUES (%s, %s)",
            (mentor_id, project_id),
        )
        connection.commit()
        return {"message": "Project assigned to you"}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


@router.post("/mentors/{mentor_id}/projects/{project_id}/complete")
def complete_project(mentor_id: int, project_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        _check_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT 1 FROM Mentor_Project
            WHERE Mentor_ID = %s AND Project_ID = %s
            """,
            (mentor_id, project_id),
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=403,
                detail="This project is not assigned to this mentor",
            )

        cursor.execute(
            """
            UPDATE Project_Details
            SET Project_Status = 'Completed', Completed_At = NOW()
            WHERE Project_ID = %s AND Project_Status <> 'Completed'
            """,
            (project_id,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=400, detail="Project is already completed"
            )
        connection.commit()
        return {"message": "Project marked as completed"}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


@router.get("/projects/{project_id}/review-form")
def review_form(project_id: int, user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        project = _completed_project(cursor, project_id)
        if user_id not in _team_ids(cursor, project_id):
            raise HTTPException(
                status_code=403, detail="You were not part of this project"
            )

        cursor.execute(
            """
            SELECT u.User_ID, u.Name,
                   CASE WHEN p.User_ID = u.User_ID THEN 'Team Leader'
                        ELSE 'Member' END AS Role,
                   r.Rating, r.Comment, r.Created_At, r.Edited_At
            FROM Project_Details p
            JOIN User u
              ON u.User_ID <> %s
             AND (
                 u.User_ID = p.User_ID
                 OR EXISTS (
                     SELECT 1 FROM Project_Members pm
                     WHERE pm.Project_ID = p.Project_ID
                       AND pm.User_ID = u.User_ID
                       AND pm.Status = 'Accepted'
                 )
             )
            LEFT JOIN Peer_Review r
              ON r.Project_ID = p.Project_ID
             AND r.Reviewer_ID = %s
             AND r.Reviewee_ID = u.User_ID
            WHERE p.Project_ID = %s
            ORDER BY (u.User_ID = p.User_ID) DESC, u.Name
            """,
            (user_id, user_id, project_id),
        )
        teammates = cursor.fetchall()
        now = datetime.now()
        for person in teammates:
            created = person["Created_At"]
            person["Can_Edit"] = (
                created is None
                or now - created <= timedelta(days=EDIT_WINDOW_DAYS)
            )

        return {
            "project": {
                "Project_ID": project["Project_ID"],
                "Project_Name": project["Project_Name"],
            },
            "teammates": teammates,
            "edit_window_days": EDIT_WINDOW_DAYS,
        }
    finally:
        cursor.close()
        connection.close()


@router.post("/projects/{project_id}/reviews")
def save_review(project_id: int, request: ReviewRequest):
    comment = request.comment.strip()
    if not comment:
        raise HTTPException(status_code=400, detail="Review cannot be empty")
    if request.reviewer_id == request.reviewee_id:
        raise HTTPException(
            status_code=400, detail="You cannot review yourself"
        )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        _completed_project(cursor, project_id)
        team = _team_ids(cursor, project_id)
        if request.reviewer_id not in team or request.reviewee_id not in team:
            raise HTTPException(
                status_code=403,
                detail="Both people must be members of this project",
            )

        cursor.execute(
            """
            SELECT Review_ID, Created_At
            FROM Peer_Review
            WHERE Project_ID = %s AND Reviewer_ID = %s AND Reviewee_ID = %s
            FOR UPDATE
            """,
            (project_id, request.reviewer_id, request.reviewee_id),
        )
        existing = cursor.fetchone()

        if existing:
            if datetime.now() - existing["Created_At"] > timedelta(
                days=EDIT_WINDOW_DAYS
            ):
                raise HTTPException(
                    status_code=403,
                    detail="The edit window for this review is over",
                )
            cursor.execute(
                """
                UPDATE Peer_Review
                SET Rating = %s, Comment = %s, Edited_At = NOW()
                WHERE Review_ID = %s
                """,
                (request.rating, comment, existing["Review_ID"]),
            )
            message = "Review updated"
        else:
            cursor.execute(
                """
                INSERT INTO Peer_Review
                    (Project_ID, Reviewer_ID, Reviewee_ID, Rating, Comment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    request.reviewer_id,
                    request.reviewee_id,
                    request.rating,
                    comment,
                ),
            )
            message = "Review saved"

        connection.commit()
        return {"message": message}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


@router.get("/users/{user_id}/completed-projects")
def completed_projects_of_user(user_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT p.Project_ID, p.Project_Name, p.Completed_At
            FROM Project_Details p
            WHERE p.Project_Status = 'Completed'
              AND (
                p.User_ID = %s
                OR EXISTS (
                    SELECT 1 FROM Project_Members pm
                    WHERE pm.Project_ID = p.Project_ID
                      AND pm.User_ID = %s
                      AND pm.Status = 'Accepted'
                )
              )
            ORDER BY p.Completed_At DESC
            """,
            (user_id, user_id),
        )
        return {"projects": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()
