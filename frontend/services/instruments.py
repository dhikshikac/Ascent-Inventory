from frontend.api_client import get_client


def get_instrument(instrument_id):
    return get_client().get(f"/instruments/{instrument_id}")


def get_instruments_by_labs(lab_ids):
    if not lab_ids:
        return []
    return get_client().post(
        "/instruments/query/by-labs",
        {"lab_ids": lab_ids},
    )


def add_instrument(lab_id, model_name, serial_number=None, notes=None):
    record = get_client().post(
        "/instruments",
        {
            "lab_id": lab_id,
            "model_name": model_name,
            "serial_number": serial_number,
            "notes": notes,
        },
    )
    return record.get("id") if record else None


def edit_instrument(instrument_id, **kwargs):
    get_client().patch(f"/instruments/{instrument_id}", kwargs)
    return True


def delete_instrument(instrument_id):
    get_client().delete(f"/instruments/{instrument_id}")
    return True
