import sqlite3
from backend import database

computer_template = {
    "computer_type": "employee", 
    "employee_id": None,
    "dept_id": None,
    "lab_id": None,
    "monitor_model": None,
    "pc_model": None,
    "ram": None,
    "storage": None,
    "os_version": None,
    "webcam_specs": None,
    "desk_phone": None,
    "notes": None,
}

def add_computer(computer_type="employee", employee_id=None, dept_id=None, lab_id=None, **kwargs):
    """
    Add a computer. computer_type must be 'employee', 'shared', or 'lab_shared'.
    Pass employee_id for employee computers, dept_id for shared dept computers,
    lab_id for lab computers.
    """
    new_comp = computer_template.copy()
    new_comp["computer_type"] = computer_type
    new_comp["employee_id"] = employee_id
    new_comp["dept_id"] = dept_id
    new_comp["lab_id"] = lab_id
    for key, value in kwargs.items():
        if key in new_comp:
            new_comp[key] = value
    return database.add_computer(new_comp)

def get_computer(computer_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM computers WHERE id = ?", (computer_id,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_computers_by_employee(employee_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM computers WHERE employee_id = ?", (employee_id,))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_computers_by_dept(dept_id):
    """
    Get all shared computers for a department (not employee-linked).
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM computers WHERE dept_id = ? AND employee_id IS NULL", (dept_id,))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_computers_for_depts(dept_ids, employee_ids=None):
    """
    Get all computers attached to departments, labs, or employees in a department tree.
    """
    if not dept_ids and not employee_ids:
        return []

    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    clauses = []
    params = []
    if dept_ids:
        placeholders = ",".join("?" for _ in dept_ids)
        clauses.extend([
            f"dept_id IN ({placeholders})",
            f"lab_id IN ({placeholders})",
        ])
        params.extend(dept_ids)
        params.extend(dept_ids)
    if employee_ids:
        placeholders = ",".join("?" for _ in employee_ids)
        clauses.append(f"employee_id IN ({placeholders})")
        params.extend(employee_ids)

    c.execute(f"""
        SELECT * FROM computers
        WHERE {' OR '.join(clauses)}
        ORDER BY pc_model, monitor_model, id
    """, params)
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_computers_by_lab(lab_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM computers WHERE lab_id = ?", (lab_id,))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def edit_computer(computer_id, **kwargs):
    editable = {"monitor_model", "pc_model", "ram", "storage", "os_version",
                "webcam_specs", "desk_phone", "notes", "employee_id", "dept_id", "lab_id", "computer_type"}
    updates = {k: v for k, v in kwargs.items() if k in editable}
    if not updates:
        return False
    set_values = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [computer_id]
    conn = database.get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE computers SET {set_values} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True

def delete_computer(computer_id):
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM computers WHERE id = ?", (computer_id,))
    conn.commit()
    conn.close()
    return True