from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user

router = APIRouter(tags=["auth"])


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user
