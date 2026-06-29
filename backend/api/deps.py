from fastapi import Depends, HTTPException, Header
from firebase_admin import auth
from backend.firebase_app import init_firebase
from backend import database

init_firebase()

VALID_ROLES = frozenset({"viewer", "admin"})


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

    uid = decoded["uid"]
    email = decoded.get("email", "")
    role = _get_or_create_user(uid, email)
    if role not in VALID_ROLES:
        raise HTTPException(403, "Invalid role assigned to user")
    return {"uid": uid, "email": email, "role": role}


def require_role(*roles):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "Forbidden")
        return user
    return checker


def _get_or_create_user(uid: str, email: str) -> str:
    conn = database.get_connection()
    c = conn.cursor()

    database.execute(c, "SELECT role FROM app_users WHERE firebase_uid = ?", (uid,))
    row = c.fetchone()
    if row:
        conn.close()
        return row["role"]

    database.execute(
        c,
        "INSERT INTO app_users (firebase_uid, email, role) VALUES (?, ?, ?)",
        (uid, email, "viewer"),
    )
    conn.commit()
    conn.close()
    return "viewer"
