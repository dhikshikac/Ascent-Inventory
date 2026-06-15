import sqlite3
from backend import database
from backend import departments

# The 6 hard-coded lab names under QC
DEFAULT_LABS = [
    "Lab 1", "Lab 2", "Lab 3", "Lab 4", "Lab 5", "Lab 6"
]

def seed_labs(qc_dept_id):
    """
    Called once during setup. Creates sub-departments for each default lab
    under the QC department.
    """
    for lab_name in DEFAULT_LABS:
        if not departments.dept_exists(lab_name):
            departments.add_dept(lab_name, parent_id=qc_dept_id)

def get_all_labs(qc_dept_id):
    """Returns all lab sub-departments under QC."""
    return departments.get_subdepts_by_id(qc_dept_id)

def add_lab(name, qc_dept_id):
    """Add a new lab under QC."""
    if departments.dept_exists(name):
        return None
    return departments.add_dept(name, parent_id=qc_dept_id)