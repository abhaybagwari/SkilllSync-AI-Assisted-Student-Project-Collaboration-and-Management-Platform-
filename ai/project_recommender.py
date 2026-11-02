
from ai.skill_gap_analyzer import analyze_skill_gap


def recommend_projects(student_skills, projects, top_n=5):
    recommendations = []

    for project in projects:
        project_skills = project.get("required_skills", [])

        if isinstance(project_skills, str):
            project_skills = [
                skill.strip()
                for skill in project_skills.replace(";", ",").split(",")
                if skill.strip()
            ]

        analysis = analyze_skill_gap(student_skills, project_skills)

        recommendations.append({
            "project_id": project.get("project_id"),
            "project_name": project.get("project_name", "Untitled Project"),
            "description": project.get("description", ""),
            "match_percentage": analysis["coverage_percentage"],
            "matched_skills": analysis["matched_skills"],
            "missing_skills": analysis["missing_skills"],
            "required_skills": analysis["required_skills"],
            "recommendation_reason": (
                f"You match {analysis['skills_matched']} out of "
                f"{analysis['total_required_skills']} required skills."
            )
        })

    recommendations.sort(
        key=lambda item: (
            item["match_percentage"],
            len(item["matched_skills"])
        ),
        reverse=True
    )

    return recommendations[:max(0, top_n)]
