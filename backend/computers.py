import sqlite3
from backend import database

computer_template = {
    "computer_type": "employee", 
    "employee_id": None,
    "dept_id": None,
    "lab_id": None,
    "computer_name": None,
    "monitor_model": None,
    "pc_model": None,
    "processor": None,
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

def get_computers_by_depts(dept_ids):
    """
    Get shared computers assigned directly to any department in dept_ids.
    Employee-linked computers are shown as employee device previews instead.
    """
    if not dept_ids:
        return []
    placeholders = ",".join("?" for _ in dept_ids)
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"""
        SELECT * FROM computers
        WHERE employee_id IS NULL
        AND (dept_id IN ({placeholders}) OR lab_id IN ({placeholders}))
        ORDER BY id
    """, dept_ids + dept_ids)
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_computers_by_employees(employee_ids):
    if not employee_ids:
        return []
    placeholders = ",".join("?" for _ in employee_ids)
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"""
        SELECT * FROM computers
        WHERE employee_id IN ({placeholders})
        ORDER BY employee_id, id
    """, employee_ids)
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
                "webcam_specs", "desk_phone", "notes", "employee_id", "dept_id",
                "lab_id", "computer_type", "computer_name", "processor"}
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

 # def count_webcams_in_depts(dept_ids):
    """Count computers with webcam_specs set across a list of dept ids (employee + shared)."""
    if not dept_ids:
        return 0
    placeholders = ",".join("?" for _ in dept_ids)
    conn = database.get_connection()
    c = conn.cursor()
    # Employee-linked webcams: join employees to get their dept
    c.execute(f"""
        SELECT COUNT(*) FROM computers c
        JOIN employees e ON c.employee_id = e.employee_id
        WHERE e.dept_id IN ({placeholders})
        AND c.webcam_specs IS NOT NULL AND c.webcam_specs != ''
    """, dept_ids)
    employee_wc = c.fetchone()[0]
    # Shared / lab webcams assigned directly to dept or lab
    c.execute(f"""
        SELECT COUNT(*) FROM computers
        WHERE (dept_id IN ({placeholders}) OR lab_id IN ({placeholders}))
        AND employee_id IS NULL
        AND webcam_specs IS NOT NULL AND webcam_specs != ''
    """, dept_ids + dept_ids)
    shared_wc = c.fetchone()[0]
    conn.close()
    return employee_wc + shared_wc

def count_webcams_in_depts(dept_ids):
    """Count computers with webcam_specs set across a list of dept ids (employee + shared)."""
    if not dept_ids:
        return 0
    placeholders = ",".join("?" for _ in dept_ids)
    conn = database.get_connection()
    c = conn.cursor()
    
    # Employee-linked webcams: join employees matching their primary key identifier
    c.execute(f"""
        SELECT COUNT(*) FROM computers c
        JOIN employees e ON c.employee_id = e.employee_id
        WHERE e.dept_id IN ({placeholders})
        AND c.webcam_specs IS NOT NULL AND c.webcam_specs != ''
    """, dept_ids)
    employee_wc = c.fetchone()[0]
    
    # Shared / lab webcams assigned directly to dept or lab
    c.execute(f"""
        SELECT COUNT(*) FROM computers
        WHERE (dept_id IN ({placeholders}) OR lab_id IN ({placeholders}))
        AND employee_id IS NULL
        AND webcam_specs IS NOT NULL AND webcam_specs != ''
    """, dept_ids + dept_ids)
    shared_wc = c.fetchone()[0]
    
    conn.close()
    return employee_wc + shared_wc

