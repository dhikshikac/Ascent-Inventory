from frontend.api_client import ApiClient, ApiError, get_client


def get_all_depts():
    return get_client().get("/departments")


def add_dept(name, parent_id=None):
    try:
        data = get_client().post("/departments", {"name": name, "parent_id": parent_id})
        return data.get("id") if data else None
    except ApiError as exc:
        if exc.status_code == 409:
            return None
        raise


def delete_dept_by_id(dept_id):
    get_client().delete(f"/departments/{dept_id}")
    return True


def get_name(dept_id):
    if dept_id is None:
        return "Unassigned"
    return get_client().get(f"/departments/{dept_id}/name")["name"]


def get_descendant_ids(dept_id, include_self=True):
    ids = get_client().get(f"/departments/{dept_id}/descendants")
    return ids if include_self else ids[1:]
