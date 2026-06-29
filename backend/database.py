import os
import re
import sqlite3

_DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")


def is_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


def _postgres_url() -> str:
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def ph() -> str:
    return "%s" if is_postgres() else "?"


def phs(count: int) -> str:
    return ", ".join([ph()] * count)


def adapt_sql(sql: str) -> str:
    if not is_postgres():
        return sql
    return sql.replace("?", "%s")


def adapt_named_sql(sql: str) -> str:
    if not is_postgres():
        return sql
    return re.sub(r":(\w+)", r"%(\1)s", sql)


def order_nocase(column: str) -> str:
    if is_postgres():
        return f"LOWER({column})"
    return f"{column} COLLATE NOCASE"


def scalar(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def row_dict(row):
    if row is None:
        return None
    return dict(row)


def execute(cursor, sql: str, params=None):
    sql = adapt_sql(sql)
    if params is None:
        cursor.execute(sql)
    elif isinstance(params, dict):
        cursor.execute(adapt_named_sql(sql), params)
    else:
        cursor.execute(sql, params)


def get_connection():
    if is_postgres():
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(_postgres_url(), row_factory=dict_row)
        return conn

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_columns(cursor, table: str) -> set[str]:
    if is_postgres():
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table,),
        )
        return {row["column_name"] for row in cursor.fetchall()}

    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _add_column_if_missing(cursor, table: str, column: str, typedef: str):
    if column not in _table_columns(cursor, table):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {typedef}")


def _id_column() -> str:
    return "SERIAL PRIMARY KEY" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"


def init():
    conn = get_connection()
    c = conn.cursor()

    if not is_postgres():
        c.execute("PRAGMA foreign_keys = ON")

    id_col = _id_column()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS departments (
            id {id_col},
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

    c.execute(f"""
        CREATE TABLE IF NOT EXISTS computers (
            id {id_col},
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

    for col, typedef in [("computer_name", "TEXT"), ("processor", "TEXT")]:
        _add_column_if_missing(c, "computers", col, typedef)

    c.execute(f"""
        CREATE TABLE IF NOT EXISTS instruments (
            id {id_col},
            lab_id INTEGER NOT NULL REFERENCES departments(id),
            model_name TEXT NOT NULL,
            serial_number TEXT,
            notes TEXT
        )
    """)

    _add_column_if_missing(c, "instruments", "serial_number", "TEXT")

    c.execute(f"""
        CREATE TABLE IF NOT EXISTS labs (
            id {id_col},
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
    execute(
        c,
        """
        INSERT INTO employees
        (employee_id, dept_id, first_name, last_name, notes)
        VALUES (:employee_id, :dept_id, :first_name, :last_name, :notes)
        """,
        employee_data,
    )
    conn.commit()
    conn.close()


def add_dept(dept_data: dict):
    conn = get_connection()
    c = conn.cursor()
    if is_postgres():
        execute(
            c,
            """
            INSERT INTO departments (name, parent_id)
            VALUES (:name, :parent_id)
            RETURNING id
            """,
            dept_data,
        )
        last_id = scalar(c.fetchone())
    else:
        execute(
            c,
            """
            INSERT INTO departments (name, parent_id)
            VALUES (:name, :parent_id)
            """,
            dept_data,
        )
        last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id


def add_computer(computer_data: dict):
    conn = get_connection()
    c = conn.cursor()
    if is_postgres():
        execute(
            c,
            """
            INSERT INTO computers
            (computer_type, employee_id, dept_id, lab_id, computer_name, monitor_model,
             pc_model, processor, ram, storage, os_version, webcam_specs, desk_phone, notes)
            VALUES (:computer_type, :employee_id, :dept_id, :lab_id, :computer_name,
                    :monitor_model, :pc_model, :processor, :ram, :storage, :os_version,
                    :webcam_specs, :desk_phone, :notes)
            RETURNING id
            """,
            computer_data,
        )
        last_id = scalar(c.fetchone())
    else:
        execute(
            c,
            """
            INSERT INTO computers
            (computer_type, employee_id, dept_id, lab_id, computer_name, monitor_model,
             pc_model, processor, ram, storage, os_version, webcam_specs, desk_phone, notes)
            VALUES (:computer_type, :employee_id, :dept_id, :lab_id, :computer_name,
                    :monitor_model, :pc_model, :processor, :ram, :storage, :os_version,
                    :webcam_specs, :desk_phone, :notes)
            """,
            computer_data,
        )
        last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id


def add_instrument(instrument_data: dict):
    conn = get_connection()
    c = conn.cursor()
    if is_postgres():
        execute(
            c,
            """
            INSERT INTO instruments (lab_id, model_name, serial_number, notes)
            VALUES (:lab_id, :model_name, :serial_number, :notes)
            RETURNING id
            """,
            instrument_data,
        )
        last_id = scalar(c.fetchone())
    else:
        execute(
            c,
            """
            INSERT INTO instruments (lab_id, model_name, serial_number, notes)
            VALUES (:lab_id, :model_name, :serial_number, :notes)
            """,
            instrument_data,
        )
        last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id
