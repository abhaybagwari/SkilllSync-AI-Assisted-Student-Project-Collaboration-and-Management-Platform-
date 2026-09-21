import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.projects import router as projects_router


app = FastAPI(title="SkillSync API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(projects_router)


@app.get("/")
def root():
    return {
        "message": "SkillSync Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "OK"
    }