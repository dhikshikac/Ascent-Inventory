from frontend.api_client import get_client


def get_computer(computer_id):
    return get_client().get(f"/computers/{computer_id}")


def get_computers_by_employee(employee_id):
    return get_client().get(f"/employees/{employee_id}/computers")


def get_computers_by_employees(employee_ids):
    if not employee_ids:
        return []
    return get_client().post(
        "/computers/query/by-employees",
        {"employee_ids": employee_ids},
    )


def get_computers_by_depts(dept_ids):
    if not dept_ids:
        return []
    return get_client().post(
        "/computers/query/by-depts",
        {"dept_ids": dept_ids},
    )


def count_webcams_in_depts(dept_ids):
    if not dept_ids:
        return 0
    return get_client().post(
        "/computers/query/webcam-count",
        {"dept_ids": dept_ids},
    )["count"]


def add_computer(computer_type="employee", employee_id=None, dept_id=None, lab_id=None, **kwargs):
    body = {
        "computer_type": computer_type,
        "employee_id": employee_id,
        "dept_id": dept_id,
        "lab_id": lab_id,
        **kwargs,
    }
    record = get_client().post("/computers", body)
    return record.get("id") if record else None


def edit_computer(computer_id, **kwargs):
    get_client().patch(f"/computers/{computer_id}", kwargs)
    return True


def delete_computer(computer_id):
    get_client().delete(f"/computers/{computer_id}")
    return True
