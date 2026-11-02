
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

from ai.skill_gap_analyzer import analyze_skill_gap
from ai.project_recommender import recommend_projects
from database.connection import get_connection


router = APIRouter(prefix="/ai", tags=["AI Tools"])


class SkillGapRequest(BaseModel):
    student_skills: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    student_skills: List[str] = Field(default_factory=list)
    top_n: int = Field(default=5, ge=1, le=50)


@router.get("/health")
def ai_health():
    return {
        "status": "working",
        "modules": [
            "Certificate Verifier",
            "Skill Gap Analyzer",
            "Project Recommendation"
        ]
    }


@router.post("/skill-gap")
def skill_gap(request: SkillGapRequest):
    try:
        return analyze_skill_gap(
            request.student_skills,
            request.required_skills
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Skill gap analysis failed: {error}"
        )


@router.post("/recommendations")
def project_recommendations(request: RecommendationRequest):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                Project_ID,
                Project_Name,
                Project_Description,
                Skill_Required
            FROM Project_Details
            ORDER BY Project_ID DESC
            """
        )

        rows = cursor.fetchall()

        projects = [
            {
                "project_id": row["Project_ID"],
                "project_name": row["Project_Name"],
                "description": row["Project_Description"],
                "required_skills": row["Skill_Required"] or ""
            }
            for row in rows
        ]

        recommendations = recommend_projects(
            request.student_skills,
            projects,
            request.top_n
        )

        return {
            "total_projects_considered": len(projects),
            "recommendations": recommendations
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Project recommendation failed: {error}"
        )
    finally:
        cursor.close()
        connection.close()
