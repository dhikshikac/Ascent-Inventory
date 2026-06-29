_user: dict | None = None
_refresh_token: str | None = None


def set_session(user: dict, refresh_token: str | None = None) -> None:
    global _user, _refresh_token
    _user = user
    if refresh_token is not None:
        _refresh_token = refresh_token


def clear() -> None:
    global _user, _refresh_token
    _user = None
    _refresh_token = None


def user() -> dict | None:
    return _user


def role() -> str:
    if _user is None:
        return "viewer"
    return _user.get("role", "viewer")


def is_admin() -> bool:
    return role() == "admin"


def refresh_token() -> str | None:
    return _refresh_token
