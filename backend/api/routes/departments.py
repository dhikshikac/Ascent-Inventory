from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import departments
from backend.api.deps import get_current_user, require_role

router = APIRouter(prefix="/departments", tags=["departments"])


class DeptCreate(BaseModel):
    name: str
    parent_id: int | None = None


@router.get("")
def list_departments(_user=Depends(get_current_user)):
    return departments.get_all_depts()


@router.post("", status_code=201)
def create_department(body: DeptCreate, _user=Depends(require_role("admin"))):
    dept_id = departments.add_dept(body.name, body.parent_id)
    if dept_id is None:
        raise HTTPException(409, "Department already exists")
    return {"id": dept_id}


@router.get("/{dept_id}/name")
def department_name(dept_id: int, _user=Depends(get_current_user)):
    return {"name": departments.get_name(dept_id)}


@router.get("/{dept_id}/descendants")
def department_descendants(dept_id: int, _user=Depends(get_current_user)):
    return departments.get_descendant_ids(dept_id)


@router.get("/{dept_id}/employees")
def department_employees(dept_id: int, _user=Depends(get_current_user)):
    from backend import employees

    return employees.get_all_dept_employees(dept_id)


@router.delete("/{dept_id}")
def remove_department(dept_id: int, _user=Depends(require_role("admin"))):
    if not departments.delete_dept_by_id(dept_id):
        raise HTTPException(404, "Department not found")
    return {"ok": True}
