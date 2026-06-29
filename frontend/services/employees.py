from frontend.api_client import get_client


def get_all_employees():
    return get_client().get("/employees")


def get_all_dept_employees(dept_id):
    return get_client().get(f"/departments/{dept_id}/employees")


def get_employee(employee_id):
    return get_client().get(f"/employees/{employee_id}")


def employee_exists(employee_id):
    return get_client().get(f"/employees/{employee_id}/exists")["exists"]


def add_employee(employee_id, dept_id, first_name, last_name, **kwargs):
    get_client().post(
        "/employees",
        {
            "employee_id": employee_id,
            "dept_id": dept_id,
            "first_name": first_name,
            "last_name": last_name,
            "notes": kwargs.get("notes"),
        },
    )


def edit_employee(employee_id, **kwargs):
    get_client().patch(f"/employees/{employee_id}", kwargs)


def delete_employee(employee_id):
    get_client().delete(f"/employees/{employee_id}")
    return True
