import secrets
import threading
import time

from fastapi import Depends, Header, HTTPException

SESSION_TTL_SECONDS = 8 * 60 * 60

PERMISSIONS = {
    "Team Leader": {"create_project", "apply_project", "manage_members"},
    "Team Member": {"apply_project"},
    "Mentor": {"review_project"},
}

_sessions = {}
_lock = threading.Lock()


def create_session(user_id, role):
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = {
            "user_id": user_id,
            "role": role,
            "expires_at": time.time() + SESSION_TTL_SECONDS,
        }
    return token


def lookup_session(token):
    with _lock:
        session = _sessions.get(token)
        if session is None:
            return None
        if session["expires_at"] < time.time():
            del _sessions[token]
            return None
        return dict(session)


def current_user(authorization: str = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in first.")

    session = lookup_session(authorization[len("Bearer "):])

    if session is None:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    return session


def require_permission(permission):
    def dependency(user: dict = Depends(current_user)):
        if permission not in PERMISSIONS.get(user["role"], set()):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to do this."
            )
        return user
    return dependency