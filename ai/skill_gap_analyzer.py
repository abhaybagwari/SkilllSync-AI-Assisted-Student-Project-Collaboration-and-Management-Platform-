import re
from difflib import SequenceMatcher


SKILL_ALIASES = {
    "c++": ["cpp", "cplusplus"],
    "c": ["c language", "c programming"],
    "javascript": ["js"],
    "html": ["html5"],
    "css": ["css3"],
    "sql": ["structured query language"],
    "mysql": ["my sql"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "data structures and algorithms": ["dsa", "data structures", "algorithms"],
    "ui ux": ["ui/ux", "user interface", "user experience"],
    "react": ["reactjs", "react.js"],
    "node.js": ["nodejs"],
    "fastapi": ["fast api"],
}

LEARNING_SUGGESTIONS = {
    "python": "Practice Python basics, functions, OOP and problem solving.",
    "java": "Learn Java syntax, OOP concepts and collections.",
    "sql": "Practice SQL queries, joins, subqueries and database design.",
    "mysql": "Learn MySQL queries, joins, indexing and database management.",
    "html": "Learn semantic HTML and page structure.",
    "css": "Practice CSS layouts, Flexbox, Grid and responsive design.",
    "javascript": "Learn DOM manipulation, events and asynchronous JavaScript.",
    "react": "Learn components, props, state and React hooks.",
    "fastapi": "Practice REST APIs, routing, validation and database integration.",
    "machine learning": "Study supervised learning, model evaluation and basic ML algorithms.",
    "deep learning": "Learn neural networks, backpropagation and deep learning frameworks.",
    "natural language processing": "Practice text preprocessing, tokenization and text classification.",
    "data structures and algorithms": "Practice arrays, linked lists, trees, graphs and algorithms.",
    "ui ux": "Study user research, wireframes, prototyping and usability.",
}


def clean_skill(skill):
    return re.sub(r"[^a-z0-9+#]", "", str(skill).lower())


def parse_skills(skills):
    if isinstance(skills, str):
        skills = re.split(r"[,;\n]", skills)

    if not isinstance(skills, (list, tuple, set)):
        return []

    result = []
    for skill in skills:
        skill = str(skill).strip()
        if skill and skill not in result:
            result.append(skill)

    return result


def canonical_skill(skill):
    key = clean_skill(skill)

    for canonical, aliases in SKILL_ALIASES.items():
        if key == clean_skill(canonical):
            return canonical

        if any(key == clean_skill(alias) for alias in aliases):
            return canonical

    return str(skill).strip()


def skills_match(first, second):
    first_key = clean_skill(canonical_skill(first))
    second_key = clean_skill(canonical_skill(second))

    if first_key == second_key:
        return True

    # Conservative fuzzy matching for minor spelling variations.
    return (
        len(first_key) >= 5
        and len(second_key) >= 5
        and SequenceMatcher(None, first_key, second_key).ratio() >= 0.93
    )


def analyze_skill_gap(student_skills, required_skills):
    student = parse_skills(student_skills)
    required = parse_skills(required_skills)

    matched = []
    missing = []
    match_details = []

    for required_skill in required:
        found = next(
            (
                student_skill
                for student_skill in student
                if skills_match(student_skill, required_skill)
            ),
            None
        )

        if found:
            matched.append(required_skill)
            match_details.append({
                "required_skill": required_skill,
                "student_skill": found
            })
        else:
            missing.append(required_skill)

    total = len(required)
    coverage = round((len(matched) / total) * 100, 2) if total else 0

    suggestions = []
    for skill in missing:
        key = canonical_skill(skill).lower()
        suggestion = LEARNING_SUGGESTIONS.get(
            key,
            f"Start learning {skill} through beginner tutorials and practical projects."
        )

        suggestions.append({
            "skill": skill,
            "suggestion": suggestion
        })

    return {
        "student_skills": student,
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_details": match_details,
        "total_required_skills": total,
        "skills_matched": len(matched),
        "coverage_percentage": coverage,
        "gap_percentage": round(100 - coverage, 2) if total else 0,
        "learning_suggestions": suggestions
    }
