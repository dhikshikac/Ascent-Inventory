import sqlite3

def getConnection():
    return sqlite3.connect("inventory.db")

def init():
    conn = getConnection()
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
            first_name TEXT,
            last_name TEXT,
            dept_id INTEGER REFERENCES departments(id),
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



