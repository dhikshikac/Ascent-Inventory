import sqlite3

def get_connection():
    return sqlite3.connect("inventory.db")

def init():
    conn = get_connection()
    c = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

def add_employee(employee_data: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO employees 
        (employee_id, dept_id, first_name, last_name, monitor_model, pc_model, ram, storage, os_version, webcam_specs, desk_phone, notes)
        VALUES (:employee_id, :dept_id, :first_name, :last_name, :monitor_model, :pc_model, :ram, :storage, :os_version, :webcam_specs, :desk_phone, :notes)
    """, employee_data)
    conn.commit()
    conn.close()



