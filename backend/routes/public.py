from fastapi import APIRouter, Depends, HTTPException, Response
from database.connection import get_connection


def no_index(response: Response):
    response.headers["X-Robots-Tag"] = "noindex"


router = APIRouter(
    prefix="/public",
    tags=["Public"],
    dependencies=[Depends(no_index)],
)


def _get_mentor(cursor, mentor_id):
    cursor.execute(
        "SELECT User_ID, Name FROM User WHERE User_ID = %s AND Role = 'Mentor'",
        (mentor_id,),
    )
    mentor = cursor.fetchone()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return mentor


@router.get("/mentors")
def list_mentors():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT u.User_ID, u.Name,
                   COUNT(p.Project_ID) AS Completed_Projects
            FROM User u
            LEFT JOIN Mentor_Project mp ON mp.Mentor_ID = u.User_ID
            LEFT JOIN Project_Details p
                   ON p.Project_ID = mp.Project_ID
                  AND p.Project_Status = 'Completed'
            WHERE u.Role = 'Mentor'
            GROUP BY u.User_ID, u.Name
            ORDER BY u.Name
            """
        )
        return {"mentors": cursor.fetchall()}
    finally:
        cursor.close()
        connection.close()


@router.get("/mentors/{mentor_id}/projects")
def mentor_projects(mentor_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        mentor = _get_mentor(cursor, mentor_id)
        cursor.execute(
            """
            SELECT p.Project_ID, p.Project_Name, p.Completed_At
            FROM Mentor_Project mp
            JOIN Project_Details p ON p.Project_ID = mp.Project_ID
            WHERE mp.Mentor_ID = %s AND p.Project_Status = 'Completed'
            ORDER BY p.Completed_At DESC, p.Project_ID DESC
            """,
            (mentor_id,),
        )
        projects = cursor.fetchall()
        return {
            "mentor": mentor,
            "completed_projects": len(projects),
            "projects": projects,
        }
    finally:
        cursor.close()
        connection.close()


@router.get("/projects/{project_id}")
def project_page(project_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT p.Project_ID, p.Project_Name, p.Completed_At,
                   p.User_ID AS Leader_ID, leader.Name AS Leader_Name
            FROM Project_Details p
            JOIN User leader ON leader.User_ID = p.User_ID
            WHERE p.Project_ID = %s AND p.Project_Status = 'Completed'
            """,
            (project_id,),
        )
        project = cursor.fetchone()
        if not project:
            raise HTTPException(
                status_code=404, detail="Completed project not found"
            )

        cursor.execute(
            """
            SELECT u.User_ID, u.Name
            FROM Project_Members pm
            JOIN User u ON u.User_ID = pm.User_ID
            WHERE pm.Project_ID = %s
              AND pm.Status = 'Accepted'
              AND pm.User_ID <> %s
            ORDER BY u.Name
            """,
            (project_id, project["Leader_ID"]),
        )
        team = [
            {
                "User_ID": project["Leader_ID"],
                "Name": project["Leader_Name"],
                "Role": "Team Leader",
            }
        ]
        for row in cursor.fetchall():
            team.append(
                {"User_ID": row["User_ID"], "Name": row["Name"], "Role": "Member"}
            )

        cursor.execute(
            """
            SELECT u.User_ID, u.Name
            FROM Mentor_Project mp
            JOIN User u ON u.User_ID = mp.Mentor_ID
            WHERE mp.Project_ID = %s
            ORDER BY u.Name
            """,
            (project_id,),
        )
        mentors = cursor.fetchall()

        cursor.execute(
            """
            SELECT f.Rating, f.Feedback_Text, f.Feedback_Date,
                   u.Name AS Mentor_Name
            FROM Project_Feedback f
            JOIN User u ON u.User_ID = f.Mentor_ID
            WHERE f.Project_ID = %s
            ORDER BY f.Feedback_Date DESC
            """,
            (project_id,),
        )
        feedback_rows = cursor.fetchall()
        mentor_review = None
        if feedback_rows:
            ratings = [row["Rating"] for row in feedback_rows]
            mentor_review = {
                "average_rating": round(sum(ratings) / len(ratings), 1),
                "review_count": len(ratings),
                "latest": feedback_rows[0],
            }

        return {
            "project": {
                "Project_ID": project["Project_ID"],
                "Project_Name": project["Project_Name"],
                "Completed_At": project["Completed_At"],
            },
            "mentors": mentors,
            "team": team,
            "mentor_review": mentor_review,
        }
    finally:
        cursor.close()
        connection.close()