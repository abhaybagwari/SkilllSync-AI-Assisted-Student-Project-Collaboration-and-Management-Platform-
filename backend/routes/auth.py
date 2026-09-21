from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.connection import get_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str
    role: str
    email: EmailStr
    password: str


@router.post("/signup")
def signup(user: SignupRequest):

    role_map = {
        "student": "Team Member",
        "leader": "Team Leader",
        "mentor": "Mentor"
    }

    if user.role not in role_map:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    db_role = role_map[user.role]

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT User_ID FROM User WHERE Email = %s",
            (user.email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        cursor.execute(
            """
            INSERT INTO User (Role, Email, Password)
            VALUES (%s, %s, %s)
            """,
            (db_role, user.email, user.password)
        )

        connection.commit()

        return {
            "message": "Account created successfully",
            "user": {
                "name": user.name,
                "role": db_role,
                "email": user.email
            }
        }

    finally:
        cursor.close()
        connection.close()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(user: LoginRequest):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT User_ID, Role, Password
            FROM User
            WHERE Email = %s
            """,
            (user.email,)
        )

        db_user = cursor.fetchone()

        if not db_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        user_id, role, password = db_user

        if password != user.password:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        return {
            "message": "Login successful",
            "user": {
                "user_id": user_id,
                "email": user.email,
                "role": role
            }
        }

    finally:
        cursor.close()
        connection.close()