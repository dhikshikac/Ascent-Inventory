from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import instruments
from backend.api.deps import get_current_user, require_role

router = APIRouter(prefix="/instruments", tags=["instruments"])


class LabIdList(BaseModel):
    lab_ids: list[int]


class InstrumentCreate(BaseModel):
    lab_id: int
    model_name: str
    serial_number: str | None = None
    notes: str | None = None


class InstrumentUpdate(BaseModel):
    model_name: str | None = None
    serial_number: str | None = None
    notes: str | None = None


@router.get("/{instrument_id}")
def get_instrument(instrument_id: int, _user=Depends(get_current_user)):
    record = instruments.get_instrument(instrument_id)
    if record is None:
        raise HTTPException(404, "Instrument not found")
    return record


@router.post("/query/by-labs")
def instruments_by_labs(body: LabIdList, _user=Depends(get_current_user)):
    return instruments.get_instruments_by_labs(body.lab_ids)


@router.post("", status_code=201)
def create_instrument(body: InstrumentCreate, _user=Depends(require_role("admin"))):
    instrument_id = instruments.add_instrument(
        body.lab_id,
        body.model_name,
        serial_number=body.serial_number,
        notes=body.notes,
    )
    return instruments.get_instrument(instrument_id)


@router.patch("/{instrument_id}")
def update_instrument(
    instrument_id: int,
    body: InstrumentUpdate,
    _user=Depends(require_role("admin")),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    if not instruments.edit_instrument(instrument_id, **updates):
        raise HTTPException(404, "Instrument not found or update failed")
    return instruments.get_instrument(instrument_id)


@router.delete("/{instrument_id}")
def remove_instrument(instrument_id: int, _user=Depends(require_role("admin"))):
    if not instruments.delete_instrument(instrument_id):
        raise HTTPException(404, "Instrument not found")
    return {"ok": True}
