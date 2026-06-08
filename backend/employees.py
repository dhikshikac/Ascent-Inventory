import sqlite3
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
    c.execute("SELECT 1 FROM employees WHERE employee_id = ?", (employee_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_employee(employee_id):
    if not employee_exists(employee_id):
        return None
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def delete_employee(employee_id):
    if not employee_exists(employee_id):
        return False
    conn = database.get_connection()
    c = conn.cursor()
    # Also delete linked computers
    c.execute("DELETE FROM computers WHERE employee_id = ?", (employee_id,))
    c.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
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
    set_values = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [employee_id]
    conn = database.get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE employees SET {set_values} WHERE employee_id = ?", values)
    conn.commit()
    conn.close()
    return True

def get_all_employees():
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    all_employees = [dict(row) for row in c.fetchall()]
    conn.close()
    return all_employees

def get_all_dept_employees(dept_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT e.* FROM employees e
        JOIN departments d ON e.dept_id = d.id
        WHERE d.id = ? OR d.parent_id = ?
    """, (dept_id, dept_id))
    all_dept_employees = [dict(row) for row in c.fetchall()]
    conn.close()
    return all_dept_employees

def search_employees(query):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    like = f"%{query}%"
    c.execute("""
        SELECT * FROM employees
        WHERE employee_id LIKE ?
        OR first_name LIKE ?
        OR last_name LIKE ?
    """, (like, like, like))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results 

