import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.auth import router as auth_router
from backend.routes.projects import router as projects_router
from backend.routes.mentor import router as mentor_router
from backend.routes.profiles import router as profiles_router
from backend.routes.public import router as public_router
from backend.routes.certificates import router as certificates_router
from backend.routes.workflow import router as workflow_router

app = FastAPI(title="SkillSync API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(mentor_router)
app.include_router(profiles_router)
app.include_router(public_router)
app.include_router(certificates_router)
app.include_router(workflow_router)


@app.get("/")
def root():
    return {"message": "SkillSync Backend is running"}


@app.get("/health")
def health():
    return {"status": "OK"}