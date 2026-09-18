from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
router=APIRouter(prefix="/auth",tags=["Authentication"])
class SignupRequest(BaseModel):
    name:str
    email: EmailStr
    password:str

@router.post("/signup")
def signup(user: SignupRequest):
    return{
        "message":"Signup request received",
        "user":{
            "name":user.name,
            "email":user.email
        }
    }
class LoginRequest(BaseModel):
    email:EmailStr
    password:str

@router.post("/login")
def login(user:LoginRequest):
    return{
        "message":"Login request recived",
        "user":{
            "email":user.email
        }
    }