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

    c.execute("SELECT COUNT(*) FROM employees WHERE dept_id = ?", (dept_id,))

    if c.fetchone()[0] > 0:
        conn.close()
        raise ValueError(f"Cannot delete '{name}' department. It still has existing sub-departments.")
    
    c.execute("SELECT * FROM employees WHERE dept_id = ?", (dept_id,))
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



