import requests
from config.firebase_config import API_BASE_URL


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class ApiClient:
    def __init__(self, id_token: str, refresh_token: str | None = None):
        self._token = id_token
        self._refresh_token = refresh_token
        self._base = API_BASE_URL.rstrip("/")
        self._session = requests.Session()

    def close(self) -> None:
        self._session.close()

    def set_token(self, id_token: str, refresh_token: str | None = None) -> None:
        self._token = id_token
        if refresh_token is not None:
            self._refresh_token = refresh_token

    def _headers(self):
        return {"Authorization": f"Bearer {self._token}"}

    def _handle_response(self, response: requests.Response):
        if response.ok:
            return response

        if response.status_code == 401:
            raise ApiError(401, "Session expired. Please sign in again.")
        if response.status_code == 403:
            raise ApiError(403, "You don't have permission for this action.")
        if response.status_code == 409:
            raise ApiError(409, response.text or "Conflict")
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text or f"Request failed ({response.status_code})"
        raise ApiError(response.status_code, str(detail))

    def _refresh_and_retry(self, method: str, path: str, **kwargs):
        from backend.auth_client import refresh_id_token

        if not self._refresh_token:
            raise ApiError(401, "Session expired. Please sign in again.")
        tokens = refresh_id_token(self._refresh_token)
        self.set_token(tokens["id_token"], tokens.get("refresh_token"))
        from frontend import session

        session.set_session(session.user() or {}, tokens.get("refresh_token"))
        response = self._session.request(
            method,
            f"{self._base}{path}",
            headers=self._headers(),
            timeout=30,
            **kwargs,
        )
        return self._handle_response(response)

    def _request(self, method: str, path: str, **kwargs):
        response = self._session.request(
            method,
            f"{self._base}{path}",
            headers=self._headers(),
            timeout=30,
            **kwargs,
        )
        if response.status_code == 401 and self._refresh_token:
            response = self._refresh_and_retry(method, path, **kwargs)
        else:
            response = self._handle_response(response)
        return response

    def get(self, path: str, **params):
        r = self._request("GET", path, params=params)
        return r.json()

    def post(self, path: str, json: dict):
        r = self._request("POST", path, json=json)
        return r.json() if r.content else None

    def patch(self, path: str, json: dict):
        r = self._request("PATCH", path, json=json)
        return r.json() if r.content else None

    def delete(self, path: str):
        r = self._request("DELETE", path)
        return r.json() if r.content else None


_client: ApiClient | None = None


def set_client(client: ApiClient | None) -> None:
    global _client
    _client = client


def get_client() -> ApiClient:
    if _client is None:
        raise RuntimeError("Not authenticated")
    return _client


def clear_client() -> None:
    global _client
    if _client is not None:
        _client.close()
    _client = None
