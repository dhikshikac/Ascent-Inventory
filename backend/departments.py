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
    
    database.execute(c, f"SELECT 1 FROM departments WHERE name = {database.ph()}", (name,))
    
    result = c.fetchone()
    conn.close()
    return result is not None

def get_dept(name):
    """
    Returns a dict of department information or None if department is not found.
    """
    conn = database.get_connection()
    c = conn.cursor()
    
    database.execute(c, f"SELECT * FROM departments WHERE name = {database.ph()}", (name,))
    
    result = c.fetchone()
    conn.close()
    return database.row_dict(result)

def get_name(dept_id):
    """
    Returns the name of a department or "Unassigned" if not found.
    """
    if dept_id is None:
        return "Unassigned"
    conn = database.get_connection()
    c = conn.cursor()
    
    database.execute(c, f"SELECT name FROM departments WHERE id = {database.ph()}", (dept_id,))
    
    result = c.fetchone()
    conn.close()
    return database.scalar(result) if result else "Unassigned"

def _children_map(all_depts: list[dict]) -> dict[int, list[int]]:
    children_map: dict[int, list[int]] = {}
    for dept in all_depts:
        parent_id = dept["parent_id"]
        if parent_id is not None:
            children_map.setdefault(parent_id, []).append(dept["id"])
    return children_map


def _collect_descendant_ids(root_id: int, children_map: dict[int, list[int]]) -> list[int]:
    ids: list[int] = []

    def collect(current_id: int):
        ids.append(current_id)
        for child_id in children_map.get(current_id, []):
            collect(child_id)

    collect(root_id)
    return ids


def get_descendant_ids(dept_id, include_self=True):
    """
    Returns department ids under dept_id, including nested sub-departments.
    """
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(c, "SELECT id, parent_id FROM departments")
    all_depts = [database.row_dict(row) for row in c.fetchall()]
    conn.close()

    ids = _collect_descendant_ids(dept_id, _children_map(all_depts))
    return ids if include_self else ids[1:]

def delete_dept_by_id(dept_id):
    """
    Deletes a department and any sub-departments, including related employees,
    employee computers, shared/lab computers, and instruments.
    """
    conn = database.get_connection()
    c = conn.cursor()

    database.execute(c, f"SELECT 1 FROM departments WHERE id = {database.ph()}", (dept_id,))
    if c.fetchone() is None:
        conn.close()
        return False

    database.execute(c, "SELECT id, parent_id FROM departments")
    all_depts = [database.row_dict(row) for row in c.fetchall()]
    dept_ids = _collect_descendant_ids(dept_id, _children_map(all_depts))
    placeholders = database.phs(len(dept_ids))

    database.execute(
        c,
        f"SELECT employee_id FROM employees WHERE dept_id IN ({placeholders})",
        dept_ids,
    )
    employee_ids = [row["employee_id"] for row in c.fetchall()]
    if employee_ids:
        employee_placeholders = database.phs(len(employee_ids))
        database.execute(
            c,
            f"DELETE FROM computers WHERE employee_id IN ({employee_placeholders})",
            employee_ids,
        )

    database.execute(
        c,
        f"DELETE FROM computers WHERE dept_id IN ({placeholders}) OR lab_id IN ({placeholders})",
        dept_ids + dept_ids,
    )
    database.execute(
        c,
        f"DELETE FROM instruments WHERE lab_id IN ({placeholders})",
        dept_ids,
    )
    database.execute(
        c,
        f"DELETE FROM employees WHERE dept_id IN ({placeholders})",
        dept_ids,
    )

    for current_id in reversed(dept_ids):
        database.execute(c, f"DELETE FROM departments WHERE id = {database.ph()}", (current_id,))

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

    database.execute(
        c,
        f"SELECT COUNT(*) FROM departments WHERE parent_id = {database.ph()}",
        (dept_id,),
    )

    if database.scalar(c.fetchone()) > 0:
        conn.close()
        raise ValueError(f"Cannot delete '{name}' department. It still has existing sub-departments.")
    
    database.execute(
        c,
        f"SELECT COUNT(*) FROM employees WHERE dept_id = {database.ph()}",
        (dept_id,),
    )
    has_employees = database.scalar(c.fetchone()) > 0

    if has_employees:
        if parent_id is not None:
            database.execute(
                c,
                f"UPDATE employees SET dept_id = {database.ph()} WHERE dept_id = {database.ph()}",
                (parent_id, dept_id),
            )
        else:
            if on_delete_dept == "delete":
                database.execute(
                    c,
                    f"DELETE FROM employees WHERE dept_id = {database.ph()}",
                    (dept_id,),
                )
            elif on_delete_dept == "unassign":
                database.execute(
                    c,
                    f"UPDATE employees SET dept_id = NULL WHERE dept_id = {database.ph()}",
                    (dept_id,),
                )
            else:
                conn.close()
                raise ValueError("Cannot determine action for employees. Select either 'delete' or 'unassign'.")
    
    database.execute(c, f"DELETE FROM departments WHERE id = {database.ph()}", (dept_id,))

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
    
    database.execute(
        c,
        f"UPDATE departments SET name = {database.ph()} WHERE name = {database.ph()}",
        (new_name, name),
    )
    
    conn.commit()
    conn.close()
    return True

def get_all_depts():
    """
    Returns a dict of all departments in the database.
    """
    conn = database.get_connection()
    c = conn.cursor()

    database.execute(
        c,
        f"SELECT * FROM departments ORDER BY {database.order_nocase('name')}",
    )
    all_depts = [database.row_dict(row) for row in c.fetchall()]

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

    database.execute(
        c,
        f"SELECT * FROM departments WHERE parent_id = {database.ph()} "
        f"ORDER BY {database.order_nocase('name')}",
        (dept_id,),
    )
    subdepts = [database.row_dict(row) for row in c.fetchall()]
    
    conn.close()
    return subdepts

def get_subdepts_by_id(dept_id):
    """
    Returns a list of sub-departments by parent dept_id (integer).
    """
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"SELECT * FROM departments WHERE parent_id = {database.ph()} "
        f"ORDER BY {database.order_nocase('name')}",
        (dept_id,),
    )
    subdepts = [database.row_dict(row) for row in c.fetchall()]
    conn.close()
    return subdepts
