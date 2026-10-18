import math
import re
from difflib import SequenceMatcher

# If True, a certificate whose text does not contain the student's name
# is marked "Partially Verified" instead of "Verified".
REQUIRE_NAME_MATCH = True

APPROVED_INSTITUTES = {
    "Graphic Era (Deemed to be University)": [
        "graphic era deemed to be university",
        "graphic era university",
        "geu dehradun",
    ],
    "Graphic Era Hill University": [
        "graphic era hill university",
        "gehu",
    ],
    "UPES (University of Petroleum and Energy Studies)": [
        "university of petroleum and energy studies",
        "upes",
    ],
    "Doon University": [
        "doon university",
        "university of doon",
    ],
}

SKILLS = [
    "Python", "Java", "JavaScript", "C++", "C", "SQL",
    "HTML", "CSS", "React", "Node.js", "FastAPI",
    "Django", "Flask", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Data Science",
    "MySQL", "MongoDB", "Git", "Docker", "AWS",
]

# Other ways a skill may be written on a certificate.
SKILL_ALIASES = {
    "Natural Language Processing": ["NLP"],
}

# Skills shown on the profile page -> words to look for in the certificate.
# A selected skill counts as matched if ANY of these words is found.
# Keys are lowercase.
SKILL_SEARCH_TERMS = {
    "html/css": ["HTML", "CSS"],
    "dbms": ["DBMS", "SQL", "MySQL", "Database", "Databases"],
    "dsa": ["DSA", "Data Structures", "Algorithms"],
    "ui/ux": ["UI/UX", "UX", "User Interface", "User Experience"],
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\W_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_institute(text: str):
    normalized = normalize_text(text)

    for official_name, aliases in APPROVED_INSTITUTES.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias)

            # Match complete normalized phrases only.
            pattern = r"(?<!\w)" + re.escape(normalized_alias) + r"(?!\w)"
            if re.search(pattern, normalized):
                return official_name

    return None


def _term_in_text(term: str, text: str) -> bool:
    # Single-letter skills (like "C") are matched case-sensitively.
    flags = 0 if len(term) == 1 else re.IGNORECASE

    # (?![\w+#]) stops "C" from matching inside "C++" or "C#".
    pattern = r"(?<![\w+#])" + re.escape(term) + r"(?![\w+#])"
    return re.search(pattern, text, flags) is not None


def extract_skills(text: str):
    found = []

    for skill in SKILLS:
        terms = [skill] + SKILL_ALIASES.get(skill, [])

        if any(_term_in_text(term, text) for term in terms):
            if skill not in found:
                found.append(skill)

    return found


def _skill_matches(skill: str, text: str, extracted_normalized: set) -> bool:
    """True if a selected skill is present in the certificate text."""
    # Original rule: the skill itself was detected in the certificate.
    if normalize_text(skill) in extracted_normalized:
        return True

    # Extra rule for the profile page skills (DBMS, DSA, HTML/CSS, UI/UX).
    terms = SKILL_SEARCH_TERMS.get(skill.strip().lower(), [])
    return any(_term_in_text(term, text) for term in terms)


def name_matches(student_name: str, text: str):
    """True/False if the student's name is found in the text.
    None if no student name was given."""
    name_tokens = [
        token for token in normalize_text(student_name or "").split()
        if len(token) > 1
    ]

    if not name_tokens:
        return None

    text_tokens = set(normalize_text(text).split())
    found = 0

    for token in name_tokens:
        if token in text_tokens:
            found += 1
            continue

        # Allow small spelling/OCR differences.
        for candidate in text_tokens:
            if abs(len(candidate) - len(token)) > 2:
                continue
            if SequenceMatcher(None, token, candidate).ratio() >= 0.85:
                found += 1
                break

    needed = math.ceil(len(name_tokens) * 2 / 3)
    return found >= needed


def verify_certificate(text: str, selected_skills=None, student_name: str = ""):
    selected_skills = selected_skills or []

    if not text or not text.strip():
        return {
            "status": "Needs Manual Review",
            "reason": "Document text could not be read.",
            "institute_detected": None,
            "name_match": None,
            "extracted_skills": [],
            "matched_skills": [],
            "missing_skills": selected_skills,
        }

    institute = detect_institute(text)
    extracted_skills = extract_skills(text)
    name_found = name_matches(student_name, text)

    extracted_normalized = {
        normalize_text(skill) for skill in extracted_skills
    }

    matched_skills = [
        skill for skill in selected_skills
        if _skill_matches(skill, text, extracted_normalized)
    ]

    missing_skills = [
        skill for skill in selected_skills
        if not _skill_matches(skill, text, extracted_normalized)
    ]

    disclaimer = " This is a screening result, not proof of authenticity."

    if institute is None:
        status = "Unverified Credential"
        reason = "No approved institute name was detected in the document."
    else:
        skills_ok = bool(matched_skills) or not selected_skills
        name_ok = (name_found is not False) or not REQUIRE_NAME_MATCH

        if skills_ok and name_ok:
            status = "Verified"
            reason = f"Approved institute detected: {institute}."
            if matched_skills:
                reason += " Matched skills: " + ", ".join(matched_skills) + "."
            if name_found:
                reason += " Student name found in the certificate."
            reason += disclaimer
        else:
            status = "Partially Verified"
            problems = []
            if not skills_ok:
                problems.append(
                    "none of the selected skills were found in the certificate"
                )
            if not name_ok:
                problems.append(
                    "the student name was not found in the certificate"
                )
            reason = (
                f"Approved institute detected: {institute}, but "
                + " and ".join(problems) + "."
            )

    return {
        "status": status,
        "reason": reason,
        "institute_detected": institute,
        "name_match": name_found,
        "extracted_skills": extracted_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }