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
    c = conn.cursor()
    database.execute(c, f"SELECT * FROM instruments WHERE lab_id = {database.ph()}", (lab_id,))
    results = [database.row_dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_instruments_by_labs(lab_ids):
    if not lab_ids:
        return []
    placeholders = database.phs(len(lab_ids))
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"""
        SELECT * FROM instruments
        WHERE lab_id IN ({placeholders})
        ORDER BY model_name, id
        """,
        lab_ids,
    )
    results = [database.row_dict(row) for row in c.fetchall()]
    conn.close()
    return results

def get_instrument(instrument_id):
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(c, f"SELECT * FROM instruments WHERE id = {database.ph()}", (instrument_id,))
    result = c.fetchone()
    conn.close()
    return database.row_dict(result)

def edit_instrument(instrument_id, **kwargs):
    editable = {"model_name", "serial_number", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in editable}
    if not updates:
        return False
    set_values = ", ".join(f"{field} = {database.ph()}" for field in updates)
    values = list(updates.values()) + [instrument_id]
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(
        c,
        f"UPDATE instruments SET {set_values} WHERE id = {database.ph()}",
        values,
    )
    conn.commit()
    conn.close()
    return True

def delete_instrument(instrument_id):
    conn = database.get_connection()
    c = conn.cursor()
    database.execute(c, f"DELETE FROM instruments WHERE id = {database.ph()}", (instrument_id,))
    conn.commit()
    conn.close()
    return True
