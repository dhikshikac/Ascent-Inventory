from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import employees
from backend.api.deps import get_current_user, require_role

router = APIRouter(prefix="/employees", tags=["employees"])


class EmployeeCreate(BaseModel):
    employee_id: str
    dept_id: int
    first_name: str
    last_name: str
    notes: str | None = None


class EmployeeUpdate(BaseModel):
    dept_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    notes: str | None = None


@router.get("")
def list_employees(_user=Depends(get_current_user)):
    return employees.get_all_employees()


@router.get("/{employee_id}")
def get_employee(employee_id: str, _user=Depends(get_current_user)):
    employee = employees.get_employee(employee_id)
    if employee is None:
        raise HTTPException(404, "Employee not found")
    return employee


@router.get("/{employee_id}/exists")
def employee_exists(employee_id: str, _user=Depends(get_current_user)):
    return {"exists": employees.employee_exists(employee_id)}


@router.post("", status_code=201)
def create_employee(body: EmployeeCreate, _user=Depends(require_role("admin"))):
    if employees.employee_exists(body.employee_id):
        raise HTTPException(409, "Employee already exists")
    employees.add_employee(
        body.employee_id,
        body.dept_id,
        body.first_name,
        body.last_name,
        notes=body.notes,
    )
    return employees.get_employee(body.employee_id)


@router.get("/{employee_id}/computers")
def employee_computers(employee_id: str, _user=Depends(get_current_user)):
    from backend import computers

    return computers.get_computers_by_employee(employee_id)


@router.patch("/{employee_id}")
def update_employee(
    employee_id: str,
    body: EmployeeUpdate,
    _user=Depends(require_role("admin")),
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    if not employees.edit_employee(employee_id, **updates):
        raise HTTPException(404, "Employee not found or update failed")
    return employees.get_employee(employee_id)


@router.delete("/{employee_id}")
def remove_employee(employee_id: str, _user=Depends(require_role("admin"))):
    if not employees.delete_employee(employee_id):
        raise HTTPException(404, "Employee not found")
    return {"ok": True}
