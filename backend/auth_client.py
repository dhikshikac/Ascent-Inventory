import requests
from config.firebase_config import FIREBASE_API_KEY

_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    f"?key={FIREBASE_API_KEY}"
)
_REFRESH_URL = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"

_MESSAGES = {
    "INVALID_LOGIN_CREDENTIALS": (
        "Incorrect email or password. "
        "Create the user in Firebase Console → Authentication → Users, "
        "or reset the password there."
    ),
    "EMAIL_NOT_FOUND": (
        "No account exists for this email. "
        "Add the user in Firebase Console → Authentication → Users."
    ),
    "INVALID_PASSWORD": "Incorrect password.",
    "INVALID_EMAIL": "Enter a valid email address.",
    "USER_DISABLED": "This account has been disabled in Firebase.",
    "OPERATION_NOT_ALLOWED": (
        "Email/Password sign-in is not enabled. "
        "In Firebase Console → Authentication → Sign-in method, "
        "enable Email/Password."
    ),
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Wait a few minutes and try again.",
    "API key not valid. Please pass a valid API key.": (
        "Firebase API key is invalid. Check FIREBASE_API_KEY in config/firebase_config.py "
        "matches your Firebase project (Project settings → General → Web API key)."
    ),
}


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _firebase_error(response: requests.Response) -> AuthError:
    try:
        body = response.json()
        err = body.get("error", {})
        code = err.get("message", "UNKNOWN")
    except Exception:
        code = "UNKNOWN"
    message = _MESSAGES.get(code, f"Sign-in failed ({code}).")
    return AuthError(code, message)


def sign_in(email: str, password: str) -> dict:
    resp = requests.post(
        _SIGN_IN_URL,
        json={
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
        timeout=15,
    )
    if not resp.ok:
        raise _firebase_error(resp)
    data = resp.json()
    return {
        "id_token": data["idToken"],
        "refresh_token": data["refreshToken"],
        "email": data["email"],
        "uid": data["localId"],
        "expires_in": int(data["expiresIn"]),
    }


def refresh_id_token(refresh_token: str) -> dict:
    resp = requests.post(
        _REFRESH_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=15,
    )
    if not resp.ok:
        raise _firebase_error(resp)
    data = resp.json()
    return {
        "id_token": data["id_token"],
        "refresh_token": data.get("refresh_token", refresh_token),
        "expires_in": int(data["expires_in"]),
    }
