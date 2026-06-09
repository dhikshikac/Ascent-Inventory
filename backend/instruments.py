import sqlite3
from backend import database

instrument_template = {
    "lab_id": None,
    "model_name": None,
    "serial_number": None,
    "notes": None,
}

def add_instrument(lab_id, model_name, serial_number=None, notes=None):
    new_inst = instrument_template.copy()
    new_inst["lab_id"] = lab_id
    new_inst["model_name"] = model_name
    new_inst["serial_number"] = serial_number
    new_inst["notes"] = notes
    return database.add_instrument(new_inst)

def get_instruments_by_lab(lab_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM instruments WHERE lab_id = ?", (lab_id,))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_instruments_by_labs(lab_ids):
    if not lab_ids:
        return []
    placeholders = ",".join("?" for _ in lab_ids)
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(f"""
        SELECT * FROM instruments
        WHERE lab_id IN ({placeholders})
        ORDER BY model_name, id
    """, lab_ids)
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_instrument(instrument_id):
    conn = database.get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM instruments WHERE id = ?", (instrument_id,))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def edit_instrument(instrument_id, **kwargs):
    editable = {"model_name", "serial_number", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in editable}
    if not updates:
        return False
    set_values = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [instrument_id]
    conn = database.get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE instruments SET {set_values} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True

def delete_instrument(instrument_id):
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))
    conn.commit()
    conn.close()
    return True