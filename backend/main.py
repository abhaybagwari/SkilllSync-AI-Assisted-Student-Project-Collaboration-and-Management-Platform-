from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
app= FastAPI(title="SkillSync API")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)
app.include_router(auth_router)
@app.get("/")
def root():
    return {
        "message": "SkillSync Backend is running"

    }
@app.get("/health")
def health():
    return{
        "status":"OK"
    }
