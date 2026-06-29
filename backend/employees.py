from backend import database

employee_info = {
    "employee_id": None,
    "dept_id": None,
    "last_name": None,
    "first_name": None,
    "notes": None,
}

def add_employee(employee_id, dept_id, first_name, last_name, **kwargs):
    if not employee_id or not dept_id or not first_name or not last_name:
        print("Employee ID, department, first name, and last name are required")
        return

    if employee_exists(employee_id):
        print("Employee already exists.")
        return

    new_employee = employee_info.copy()
    new_employee["employee_id"] = employee_id
    new_employee["dept_id"] = dept_id
    new_employee["last_name"] = last_name
    new_employee["first_name"] = first_name

    for key, value in kwargs.items():
        if key in new_employee:
            new_employee[key] = value

    database.add_employee(new_employee)

def employee_exists(employee_id):
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"SELECT 1 FROM employees WHERE employee_id = {database.ph()}",
        (employee_id,),
    )
    result = c.fetchone()
    conn.close()
    return result is not None

def get_employee(employee_id):
    if not employee_exists(employee_id):
        return None
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"SELECT * FROM employees WHERE employee_id = {database.ph()}",
        (employee_id,),
    )
    result = c.fetchone()
    conn.close()
    return database.row_dict(result)

def delete_employee(employee_id):
    if not employee_exists(employee_id):
        return False
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"DELETE FROM computers WHERE employee_id = {database.ph()}",
        (employee_id,),
    )
    database.execute(
        c,
        f"DELETE FROM employees WHERE employee_id = {database.ph()}",
        (employee_id,),
    )
    conn.commit()
    conn.close()  
    return True

def edit_employee(employee_id, **kwargs):
    if not employee_exists(employee_id):
        return False
    editable_fields = {"dept_id", "last_name", "first_name", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in editable_fields}
    if not updates:
        return False
    set_values = ", ".join(f"{field} = {database.ph()}" for field in updates)
    values = list(updates.values()) + [employee_id]
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"UPDATE employees SET {set_values} WHERE employee_id = {database.ph()}",
        values,
    )
    conn.commit()
    conn.close()
    return True

def get_all_employees():
    """Return all employees across all departments, sorted alphabetically by last name then first name."""
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"""
        SELECT * FROM employees
        ORDER BY {database.order_nocase('last_name')},
                 {database.order_nocase('first_name')},
                 employee_id
        """,
    )
    all_employees = [database.row_dict(row) for row in c.fetchall()]
    conn.close()
    return all_employees

def get_all_dept_employees(dept_id):
    dept_ids = _dept_tree_ids(dept_id)
    placeholders = database.phs(len(dept_ids))
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"""
        SELECT * FROM employees
        WHERE dept_id IN ({placeholders})
        ORDER BY last_name, first_name, employee_id
        """,
        dept_ids,
    )
    all_dept_employees = [database.row_dict(row) for row in c.fetchall()]
    conn.close()
    return all_dept_employees

def _dept_tree_ids(dept_id):
    # Local import avoids a module-level cycle with backend.departments.
    import backend.departments as departments
    return departments.get_descendant_ids(dept_id)
