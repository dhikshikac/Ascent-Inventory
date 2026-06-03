import sqlite3
from backend import database
from backend import departments

"""
    Template for containing employee information in a dictionary.
    Initializes all values to be None.
"""
employee_info = {
    "employee_id" : None,
    "dept_id" : None,
    "last_name" : None,
    "first_name" : None,
    "monitor_model" : None,
    "pc_model" : None,
    "ram" : None,
    "storage" : None,
    "os_version" : None,
    "webcam_specs" : None,
    "desk_phone" : None,
    "notes" : None,
}

"""
    Adds a new employee into the database.
    Requires employee_id, first_name, and last_name.
    Optional fields can be passed as kwargs.
    Does nothing if the employee already exists.
"""
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

"""
    Returns True if an employee with the given employee_id exists, False otherwise.
"""
def employee_exists(employee_id):
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT 1 FROM employees WHERE employee_id = ?", (employee_id,))
    
    result = c.fetchone()
    conn.close()
    return result is not None

"""
    Returns a dict of employee information or None is employee is not found.
"""
def get_employee(employee_id):
    if not employee_exists(employee_id):
        print("Employee does not exist.")
        return
    
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,)) 
    
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

"""
    Deletes the employee with the given employee_id from the database.
    Returns True on success, False if the employee does not exist.
"""
def delete_employee(employee_id):
    if not employee_exists(employee_id):
        print("Employee does not exist.")
        return False
    
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
    
    conn.commit()
    conn.close()
    return True

"""
    Updates fields of an existing employee. Fields to update are passed as kwargs.
    Only editable fields are accepted; invalid keys are ignored.
    Returns True on success, False if the employee does not exist or no valid fields were provided.
"""
def edit_employee(employee_id, **kwargs):
    if not employee_exists(employee_id):
        print("Employee does not exist.")
        return False

    editable_fields = {"dept_id", "last_name", "first_name", "monitor_model", "pc_model", "ram", "storage", "os_version", "webcam_specs", "desk_phone", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in editable_fields}
    
    if not updates:
        print("No valid fields to update.")
        return False
    
    set_values = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [employee_id]
    
    conn = database.get_connection()
    c = conn.cursor()
    
    c.execute(f"UPDATE employees SET {set_values} WHERE employee_id = ?", values)

    conn.commit()
    conn.close()
    return True

"""
    Returns a dict of all employees in the database.
"""
def get_all_employees():
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM employees")
    all_employees = [dict(row) for row in c.fetchall()]

    conn.close()
    return all_employees

"""
    Returns a list of dicts of all employees in the given department,
    including employees in its direct sub-departments.
"""
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

"""
    Searches employees by employee_id, first name, or last name.
    Supports partial matches. Returns a list of matching employee dicts,
    or an empty list if no matches are found.
"""
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

    if not results:
        print("No matches found.")
        return []
    return results

"""
    Returns a dict of the employee's information for display purposes.
    Returns None if the employee does not exist.
"""
def employee_display(employee_id):
    if not employee_exists(employee_id):
        print("Employee does not exist.")
        return
    
    employee = get_employee(employee_id)
    return employee
