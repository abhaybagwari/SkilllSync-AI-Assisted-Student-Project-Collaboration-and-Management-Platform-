from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from database.connection import get_connection
from backend.rate_limiter import TokenBucketLimiter, rate_limit
from backend.utils.jwt_handler import create_access_token
from backend.utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

signup_limiter = TokenBucketLimiter(capacity=10, refill_per_second=10 / 60)
login_limiter = TokenBucketLimiter(capacity=10, refill_per_second=10 / 60)


class SignupRequest(BaseModel):
    name: str
    role: str
    email: EmailStr
    password: str


role_map = {
    "student": "Team Member",
    "leader": "Team Leader",
    "mentor": "Mentor"
}


@router.post("/signup", dependencies=[Depends(rate_limit(signup_limiter))])
def signup(user: SignupRequest):
    if user.role not in role_map:
        raise HTTPException(status_code=400, detail="Invalid role")

    db_role = role_map[user.role]
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT User_ID FROM User WHERE Email = %s",
            (user.email,)
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        cursor.execute(
            """
            INSERT INTO User (Name, Role, Email, Password)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user.name.strip(),
                db_role,
                user.email,
                hash_password(user.password)
            )
        )

        user_id = cursor.lastrowid
        connection.commit()

        return {
            "message": "Account created successfully",
            "user": {
                "user_id": user_id,
                "name": user.name.strip(),
                "role": db_role,
                "email": user.email,
                "token": create_access_token(user_id, db_role)
            }
        }

    finally:
        cursor.close()
        connection.close()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str



@router.post("/login", dependencies=[Depends(rate_limit(login_limiter))])
def login(user: LoginRequest):
    expected_role = role_map.get(user.role)

    if not expected_role:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT User_ID, Name, Role, Password
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

        user_id, name, role, password = db_user

        is_legacy_password = not password.startswith("$argon2")

        if is_legacy_password:
            valid_password = password == user.password
        else:
            valid_password = verify_password(user.password, password)

        if not valid_password:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if role != expected_role:
            raise HTTPException(
                status_code=403,
                detail="Selected role does not match this account"
            )

        if is_legacy_password:
            cursor.execute(
                "UPDATE User SET Password = %s WHERE User_ID = %s",
                (hash_password(user.password), user_id)
            )
            connection.commit()

        return {
            "message": "Login successful",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": user.email,
                "role": role,
                "token": create_access_token(user_id, role)
            }
        }

    finally:
        cursor.close()
        connection.close()
