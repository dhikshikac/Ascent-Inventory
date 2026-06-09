import sqlite3
from backend import database

"""
    Template for containing department information in a dictionary.
    Initializes all values to be None.
"""
dept_info = {
    "name" : None,
    "parent_id" : None,
}

def add_dept(name, parent_id=None):
    """
    Adds a new department into the database.
    Requires name. 
    Optional fields include parent_id
    Does nothing if the department already exists.
    """
    if dept_exists(name):
        print("This department already exists.")
        return None

    new_dept = dept_info.copy()
    new_dept["name"] = name
    new_dept["parent_id"] = parent_id

    return database.add_dept(new_dept)   # ← now returns the new id

def dept_exists(name):
    """
    Returns True if an department with the given name exists, False otherwise.
    """
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT 1 FROM departments WHERE name = ?", (name,))
    
    result = c.fetchone()
    conn.close()
    return result is not None

def get_dept(name):
    """
    Returns a dict of department information or None if department is not found.
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM departments WHERE name = ?", (name,))
    
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_name(dept_id):
    """
    Returns the name of a department or "Unassigned" if not found.
    """
    if dept_id is None:
        return "Unassigned"
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT name FROM departments WHERE id = ?", (dept_id,))
    
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Unassigned"

def get_by_id(dept_id):
    """
    Returns a dict of department information by id or None if not found.
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))

    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def get_descendant_dept_ids(dept_id, include_self=True):
    """
    Returns dept_id plus all nested sub-department ids in parent-before-child order.
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, parent_id FROM departments")
    all_depts = [dict(row) for row in c.fetchall()]
    conn.close()

    valid_ids = {dept["id"] for dept in all_depts}
    if dept_id not in valid_ids:
        return []

    children_map = {}
    for dept in all_depts:
        parent_id = dept["parent_id"]
        if parent_id is not None:
            children_map.setdefault(parent_id, []).append(dept["id"])

    dept_ids = [dept_id] if include_self else []

    def visit(parent_id):
        for child_id in children_map.get(parent_id, []):
            dept_ids.append(child_id)
            visit(child_id)

    visit(dept_id)
    return dept_ids

def get_delete_impact(dept_id):
    """
    Returns counts of records that will be removed with a department delete.
    """
    dept_ids = get_descendant_dept_ids(dept_id)
    if not dept_ids:
        return {"departments": 0, "employees": 0, "computers": 0, "instruments": 0}

    placeholders = ",".join("?" for _ in dept_ids)
    conn = database.get_connection()
    c = conn.cursor()

    c.execute(f"SELECT employee_id FROM employees WHERE dept_id IN ({placeholders})", dept_ids)
    employee_ids = [row[0] for row in c.fetchall()]
    employee_placeholders = ",".join("?" for _ in employee_ids)

    c.execute(f"SELECT COUNT(*) FROM employees WHERE dept_id IN ({placeholders})", dept_ids)
    employee_count = c.fetchone()[0]

    computer_params = list(dept_ids) + list(dept_ids)
    computer_where = [
        f"dept_id IN ({placeholders})",
        f"lab_id IN ({placeholders})",
    ]
    if employee_ids:
        computer_where.append(f"employee_id IN ({employee_placeholders})")
        computer_params.extend(employee_ids)
    c.execute(f"SELECT COUNT(*) FROM computers WHERE {' OR '.join(computer_where)}", computer_params)
    computer_count = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM instruments WHERE lab_id IN ({placeholders})", dept_ids)
    instrument_count = c.fetchone()[0]

    conn.close()
    return {
        "departments": len(dept_ids),
        "employees": employee_count,
        "computers": computer_count,
        "instruments": instrument_count,
    }

def delete_dept_by_id(dept_id):
    """
    Deletes a department, nested sub-departments, and related inventory records.
    """
    dept_ids = get_descendant_dept_ids(dept_id)
    if not dept_ids:
        return False

    placeholders = ",".join("?" for _ in dept_ids)
    conn = database.get_connection()
    c = conn.cursor()

    c.execute(f"SELECT employee_id FROM employees WHERE dept_id IN ({placeholders})", dept_ids)
    employee_ids = [row[0] for row in c.fetchall()]

    if employee_ids:
        employee_placeholders = ",".join("?" for _ in employee_ids)
        c.execute(f"DELETE FROM computers WHERE employee_id IN ({employee_placeholders})", employee_ids)

    c.execute(f"DELETE FROM computers WHERE dept_id IN ({placeholders}) OR lab_id IN ({placeholders})", dept_ids + dept_ids)
    c.execute(f"DELETE FROM instruments WHERE lab_id IN ({placeholders})", dept_ids)
    c.execute(f"DELETE FROM labs WHERE dept_id IN ({placeholders})", dept_ids)
    c.execute(f"DELETE FROM employees WHERE dept_id IN ({placeholders})", dept_ids)

    for child_id in reversed(dept_ids):
        c.execute("DELETE FROM departments WHERE id = ?", (child_id,))

    conn.commit()
    conn.close()
    return True

def delete_dept(name, on_delete_dept=None):
    """
    Deletes the department with the given name from the database.

    If the department is a sub-department, all its employees are automatically reassigned to the parent department.

    If the department is a parent department, on_delete_dept determines what happens to its employees:
        "delete" will delete all employees in the department.
        "unassign" will set the dept_id of all employees in the department to None.

    Also raises a ValueError if the department if the department still has existing sub-departments.

    Returns True on success, False if the department does not exist.
    """
    if not dept_exists(name):
        print("Department does not exist.")
        return False
    
    dept = get_dept(name)
    dept_id = dept["id"]
    parent_id = dept["parent_id"]
    
    conn = database.get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM departments WHERE parent_id = ?", (dept_id,))

    if c.fetchone()[0] > 0:
        conn.close()
        raise ValueError(f"Cannot delete '{name}' department. It still has existing sub-departments.")
    
    c.execute("SELECT COUNT(*) FROM employees WHERE dept_id = ?", (dept_id,))
    has_employees = c.fetchone()[0] > 0

    if has_employees:
        if parent_id is not None:
            c.execute("UPDATE employees SET dept_id = ? WHERE dept_id = ?", (parent_id, dept_id))
        else:
            if on_delete_dept == "delete":
                c.execute("DELETE FROM employees WHERE dept_id = ?", (dept_id,))
            elif on_delete_dept == "unassign":
                c.execute("UPDATE employees SET dept_id = NULL WHERE dept_id = ?", (dept_id,))
            else:
                conn.close()
                raise ValueError("Cannot determine action for employees. Select either 'delete' or 'unassign'.")
    
    c.execute("DELETE FROM departments WHERE id = ?", (dept_id,))

    conn.commit()
    conn.close()

    return True

def edit_dept(name, new_name):
    """
    Updates fields of an existing department.
    The only editable field acceptable is name; invalid keys are ignored.
    Returns True on success, False if the department does not exist or no valid fields were provided.
    """
    if not dept_exists(name):
        print("Department does not exist.")
        return False
    
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("UPDATE departments SET name = ? WHERE name = ?", (new_name, name))
    
    conn.commit()
    conn.close()
    return True

def get_all_depts():
    """
    Returns a dict of all departments in the database.
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM departments")
    all_depts = [dict(row) for row in c.fetchall()]

    conn.close()
    return all_depts

def get_subdepts(name):
    """
    Returns a dict of all subdepartments of a parent department in the database.
    """
    if not dept_exists(name):
        print("Department does not exist.")
        return False
    
    dept = get_dept(name)
    dept_id = dept["id"]

    conn = database.get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM departments WHERE parent_id = ?", (dept_id,))
    subdepts = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return subdepts

def get_subdepts_by_id(dept_id):
    """
    Returns a list of sub-departments by parent dept_id (integer).
    """
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM departments WHERE parent_id = ?", (dept_id,))
    subdepts = [dict(row) for row in c.fetchall()]
    conn.close()
    return subdepts