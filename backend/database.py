import sqlite3
import os

_DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")

def get_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init():
    conn = get_connection()
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = ON")

    # Departments (unchanged)
    c.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER REFERENCES departments(id)
        )
    """)

    # Employees — computer specs removed
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            dept_id INTEGER REFERENCES departments(id),
            last_name TEXT,
            first_name TEXT,
            notes TEXT
        )
    """)

    # Computers — stand-alone, optionally linked to employee OR lab
    # computer_type: 'employee' | 'shared' | 'lab_shared'
    # employee_id: set if assigned to an employee
    # lab_id: set if this is a lab computer (references departments.id for a lab sub-dept)
    c.execute("""
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_type TEXT NOT NULL DEFAULT 'employee',
            employee_id TEXT REFERENCES employees(employee_id),
            dept_id INTEGER REFERENCES departments(id),
            lab_id INTEGER REFERENCES departments(id),
            monitor_model TEXT,
            pc_model TEXT,
            ram TEXT,
            storage TEXT,
            os_version TEXT,
            webcam_specs TEXT,
            desk_phone TEXT,
            notes TEXT
        )
    """)

    # Instruments — linked to a lab sub-department
    c.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL REFERENCES departments(id),
            model_name TEXT NOT NULL,
            serial_number TEXT,
            notes TEXT
        )
    """)

    # Labs — hard-coded names seeded at init, extensible
    c.execute("""
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_id INTEGER NOT NULL REFERENCES departments(id),
            name TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def add_employee(employee_data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO employees 
        (employee_id, dept_id, first_name, last_name, notes)
        VALUES (:employee_id, :dept_id, :first_name, :last_name, :notes)
    """, employee_data)
    conn.commit()
    conn.close()

def add_dept(dept_data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO departments 
        (name, parent_id)
        VALUES (:name, :parent_id)
    """, dept_data)
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

def add_computer(computer_data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO computers
        (computer_type, employee_id, dept_id, lab_id, monitor_model, pc_model, ram, storage, os_version, webcam_specs, desk_phone, notes)
        VALUES (:computer_type, :employee_id, :dept_id, :lab_id, :monitor_model, :pc_model, :ram, :storage, :os_version, :webcam_specs, :desk_phone, :notes)
    """, computer_data)
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

def add_instrument(instrument_data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO instruments
        (lab_id, model_name, serial_number, notes)
        VALUES (:lab_id, :model_name, :serial_number, :notes)
    """, instrument_data)
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id