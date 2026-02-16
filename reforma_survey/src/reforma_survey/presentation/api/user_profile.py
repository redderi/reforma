from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.current_user import get_current_user_id

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me")
async def me(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserProfileRepositoryImpl(db)
    user = await user_repo.get_by_id(current_user_id) 

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "profile_picture": user.profile_picture,
        "bio": user.bio,
        "surveys": [str(s) for s in user.surveys],
        "templates": [str(t) for t in user.templates],
        "reports": [str(r) for r in user.reports],
    }
