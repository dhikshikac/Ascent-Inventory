from frontend.api_client import ApiError, get_client

_cache: list[dict] | None = None


def invalidate() -> None:
    global _cache
    _cache = None


def prefetch() -> list[dict]:
    """Load departments into the in-memory cache."""
    global _cache
    _cache = get_client().get("/departments")
    return _cache


def get_all_depts(*, force: bool = False):
    global _cache
    if _cache is None or force:
        _cache = get_client().get("/departments")
    return _cache


def add_dept(name, parent_id=None):
    try:
        data = get_client().post("/departments", {"name": name, "parent_id": parent_id})
        invalidate()
        return data.get("id") if data else None
    except ApiError as exc:
        if exc.status_code == 409:
            return None
        raise


def delete_dept_by_id(dept_id):
    get_client().delete(f"/departments/{dept_id}")
    invalidate()
    return True


def get_name(dept_id):
    if dept_id is None:
        return "Unassigned"
    for dept in get_all_depts():
        if dept["id"] == dept_id:
            return dept["name"]
    return "Unassigned"


def get_descendant_ids(dept_id, include_self=True):
    ids = get_client().get(f"/departments/{dept_id}/descendants")
    return ids if include_self else ids[1:]


def get_dept_inventory(dept_id):
    return get_client().get(f"/departments/{dept_id}/inventory")
