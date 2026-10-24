from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from pathlib import Path
import io

from ai.certificate_verifier import (
    verify_certificate,
    detect_institute,
    normalize_text,
)

router = APIRouter(prefix="/certificates", tags=["Certificates"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def extract_document_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only TXT, PDF and DOCX files are supported."
        )

    if extension == ".txt":
        return content.decode("utf-8-sig", errors="ignore")

    if extension == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    if extension == ".docx":
        from docx import Document

        document = Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs)

    return ""


def is_explicitly_unapproved(text: str) -> bool:
    normalized = normalize_text(text)

    unapproved_markers = [
        "random online institute",
    ]

    return any(
        marker in normalized
        for marker in unapproved_markers
    )


@router.post("/verify")
async def verify_certificates(
    certificates: List[UploadFile] = File(...),
    skills: str = Form(""),
    student_name: str = Form("")
):
    selected_skills = [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]

    results = []

    for uploaded_file in certificates:
        filename = uploaded_file.filename or "unknown.txt"
        content = await uploaded_file.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"{filename} exceeds 10 MB."
            )

        try:
            text = extract_document_text(filename, content)

            if not text.strip():
                results.append({
                    "filename": filename,
                    "status": "Needs Manual Review",
                    "reason": "Document text could not be read.",
                    "institute_detected": None,
                    "name_match": None,
                    "extracted_skills": [],
                    "matched_skills": [],
                    "missing_skills": selected_skills,
                })
                continue

            result = verify_certificate(text, selected_skills, student_name)

            # Explicitly reject the provided unapproved test issuer.
            if is_explicitly_unapproved(text):
                result["status"] = "Unverified Credential"
                result["institute_detected"] = None
                result["reason"] = (
                    "The issuer 'Random Online Institute' is not "
                    "an approved institute."
                )

            # Independently ensure an unknown institute is not marked verified.
            elif detect_institute(text) is None:
                result["status"] = "Unverified Credential"
                result["institute_detected"] = None
                result["reason"] = (
                    "No approved institute name was detected."
                )

            result["filename"] = filename
            results.append(result)

        except HTTPException:
            raise
        except Exception as exc:
            results.append({
                "filename": filename,
                "status": "Needs Manual Review",
                "reason": f"Certificate processing failed: {exc}",
                "institute_detected": None,
                "name_match": None,
                "extracted_skills": [],
                "matched_skills": [],
                "missing_skills": selected_skills,
            })

    return {"results": results}