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

"""
    Adds a new department into the database.
    Requires name. 
    Optional fields include parent_id
    Does nothing if the department already exists.
"""
def add_dept(name, parent_id=None):
    if dept_exists(name):
        print("This department already exists.")
        return

    new_dept = dept_info.copy()
    new_dept["name"] = name
    new_dept["parent_id"] = parent_id

    database.add_dept(new_dept)

"""
    Returns True if an department with the given name exists, False otherwise.
"""
def dept_exists(name):
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT 1 FROM departments WHERE name = ?", (name,))
    
    result = c.fetchone()
    conn.close()
    return result is not None

"""
    Returns a dict of department information or None if department is not found.
"""
def get_dept(name):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM departments WHERE name = ?", (name,))
    
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

"""
    Deletes the department with the given name from the database.
    Returns True on success, False if the department does not exist.
"""
def delete_dept(name):
    if not dept_exists(name):
        print("Department does not exist.")
        return False
    
    dept = get_dept(name)
    dept_id = dept["id"]
    
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
    
    conn.commit()
    conn.close()
    return True

"""
    Updates fields of an existing department.
    The only editable field acceptable is name; invalid keys are ignored.
    Returns True on success, False if the department does not exist or no valid fields were provided.
"""
def edit_dept(name, new_name):
    if not dept_exists(name):
        print("Department does not exist.")
        return False
    
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("UPDATE departments SET name = ? WHERE name = ?", (new_name, name))
    
    conn.commit()
    conn.close()
    return True

"""
    Returns a dict of all departments in the database.
"""
def get_all_depts():
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM departments")
    all_depts = [dict(row) for row in c.fetchall()]

    conn.close()
    return all_depts

"""
    Returns a dict of all subdepartments of a parent department in the database.
"""
def get_subdepts(name):
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





