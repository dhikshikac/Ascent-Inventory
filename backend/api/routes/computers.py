from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import computers
from backend.api.deps import get_current_user, require_role

router = APIRouter(prefix="/computers", tags=["computers"])


class EmployeeIdList(BaseModel):
    employee_ids: list[str]


class DeptIdList(BaseModel):
    dept_ids: list[int]


class ComputerCreate(BaseModel):
    computer_type: str = "employee"
    employee_id: str | None = None
    dept_id: int | None = None
    lab_id: int | None = None
    computer_name: str | None = None
    monitor_model: str | None = None
    pc_model: str | None = None
    processor: str | None = None
    ram: str | None = None
    storage: str | None = None
    os_version: str | None = None
    webcam_specs: str | None = None
    desk_phone: str | None = None
    notes: str | None = None


class ComputerUpdate(BaseModel):
    computer_type: str | None = None
    employee_id: str | None = None
    dept_id: int | None = None
    lab_id: int | None = None
    computer_name: str | None = None
    monitor_model: str | None = None
    pc_model: str | None = None
    processor: str | None = None
    ram: str | None = None
    storage: str | None = None
    os_version: str | None = None
    webcam_specs: str | None = None
    desk_phone: str | None = None
    notes: str | None = None


@router.get("/{computer_id}")
def get_computer(computer_id: int, _user=Depends(get_current_user)):
    record = computers.get_computer(computer_id)
    if record is None:
        raise HTTPException(404, "Computer not found")
    return record


@router.post("/query/by-employees")
def computers_by_employees(body: EmployeeIdList, _user=Depends(get_current_user)):
    return computers.get_computers_by_employees(body.employee_ids)


@router.post("/query/by-depts")
def computers_by_depts(body: DeptIdList, _user=Depends(get_current_user)):
    return computers.get_computers_by_depts(body.dept_ids)


@router.post("/query/webcam-count")
def webcam_count(body: DeptIdList, _user=Depends(get_current_user)):
    return {"count": computers.count_webcams_in_depts(body.dept_ids)}


@router.post("", status_code=201)
def create_computer(body: ComputerCreate, _user=Depends(require_role("admin"))):
    fields = body.model_dump(exclude={"computer_type", "employee_id", "dept_id", "lab_id"})
    computer_id = computers.add_computer(
        computer_type=body.computer_type,
        employee_id=body.employee_id,
        dept_id=body.dept_id,
        lab_id=body.lab_id,
        **fields,
    )
    return computers.get_computer(computer_id)


@router.patch("/{computer_id}")
def update_computer(
    computer_id: int,
    body: ComputerUpdate,
    _user=Depends(require_role("admin")),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    if not computers.edit_computer(computer_id, **updates):
        raise HTTPException(404, "Computer not found or update failed")
    return computers.get_computer(computer_id)


@router.delete("/{computer_id}")
def remove_computer(computer_id: int, _user=Depends(require_role("admin"))):
    if not computers.delete_computer(computer_id):
        raise HTTPException(404, "Computer not found")
    return {"ok": True}
