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

    c.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER REFERENCES departments(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            dept_id INTEGER REFERENCES departments(id),
            last_name TEXT,
            first_name TEXT,
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            computer_type TEXT NOT NULL DEFAULT 'employee',
            employee_id TEXT REFERENCES employees(employee_id),
            dept_id INTEGER REFERENCES departments(id),
            lab_id INTEGER REFERENCES departments(id),
            computer_name TEXT,
            monitor_model TEXT,
            pc_model TEXT,
            processor TEXT,
            ram TEXT,
            storage TEXT,
            os_version TEXT,
            webcam_specs TEXT,
            desk_phone TEXT,
            notes TEXT
        )
    """)

    # Migrate existing databases that don't have the new computers columns
    existing_computers = {row[1] for row in c.execute("PRAGMA table_info(computers)").fetchall()}
    for col, typedef in [("computer_name", "TEXT"), ("processor", "TEXT")]:
        if col not in existing_computers:
            c.execute(f"ALTER TABLE computers ADD COLUMN {col} {typedef}")

    c.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_id INTEGER NOT NULL REFERENCES departments(id),
            model_name TEXT NOT NULL,
            serial_number TEXT,
            notes TEXT
        )
    """)

    # Migrate existing databases that don't have serial_number on instruments
    existing_instruments = {row[1] for row in c.execute("PRAGMA table_info(instruments)").fetchall()}
    if "serial_number" not in existing_instruments:
        c.execute("ALTER TABLE instruments ADD COLUMN serial_number TEXT")

    c.execute("""
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_id INTEGER NOT NULL REFERENCES departments(id),
            name TEXT NOT NULL
        )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        firebase_uid TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer'
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
        (computer_type, employee_id, dept_id, lab_id, computer_name, monitor_model, pc_model, processor, ram, storage, os_version, webcam_specs, desk_phone, notes)
        VALUES (:computer_type, :employee_id, :dept_id, :lab_id, :computer_name, :monitor_model, :pc_model, :processor, :ram, :storage, :os_version, :webcam_specs, :desk_phone, :notes)
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