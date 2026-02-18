from fastapi import APIRouter, Depends, HTTPException, Body
from reforma_survey.presentation.schemas.user_profile_schema import BioUpdate, BirthDateUpdate, GenderUpdate, LocationUpdate, ProfilePictureUpdate, UserProfileOut
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.current_user import get_current_user_id
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import UserProfileRepositoryImpl
from reforma_survey.application.user_profile.get_user_profile_by_id_use_case import GetUserProfileByIdUseCase
from reforma_survey.application.user_profile.update_profile_picture_use_case import UpdateProfilePictureUseCase
from reforma_survey.application.user_profile.update_bio_use_case import UpdateBioUseCase
from reforma_survey.application.user_profile.update_gender_use_case import UpdateGenderUseCase
from reforma_survey.application.user_profile.update_birth_date_use_case import UpdateBirthDateUseCase
from reforma_survey.application.user_profile.update_location_use_case import UpdateLocationUseCase
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me", response_model=UserProfileOut)
async def get_my_profile(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Get profile attempt for user_id={current_user_id}", service="survey-service")
    
    try:
        use_case = GetUserProfileByIdUseCase(UserProfileRepositoryImpl(db))
        profile = await use_case.execute(current_user_id)
        
        if not profile:
            log_warning(f"Profile not found for user_id={current_user_id}", service="survey-service")
            raise HTTPException(status_code=404, detail="Profile not found")

        return UserProfileOut(
            id=str(profile.id),
            username=profile.username,
            email=profile.email,
            profile_picture=profile.profile_picture,
            bio=profile.bio,
            gender=profile.gender,
            birth_date=profile.birth_date.isoformat() if profile.birth_date else None,
            country=profile.country,
            city=profile.city,
            surveys=[str(s) for s in profile.surveys],
            templates=[str(t) for t in profile.templates],
            reports=[str(r) for r in profile.reports],
        )

    except Exception as e:
        log_error(f"Error getting profile for {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/profile-picture", response_model=UserProfileOut)
async def update_my_profile_picture(
    payload: ProfilePictureUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Update profile picture attempt for user_id={current_user_id}", service="survey-service")

    try:
        use_case = UpdateProfilePictureUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.picture_url)
        
        return UserProfileOut(
            id=str(updated.id),
            username=updated.username,
            email=updated.email,
            profile_picture=updated.profile_picture,
            bio=updated.bio,
            gender=updated.gender,
            birth_date=updated.birth_date.isoformat() if updated.birth_date else None,
            country=updated.country,
            city=updated.city,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except Exception as e:
        log_error(f"Error updating profile picture {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/bio", response_model=UserProfileOut)
async def update_my_bio(
    payload: BioUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        use_case = UpdateBioUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.bio)
        return UserProfileOut(
            id=str(updated.id),
            username=updated.username,
            email=updated.email,
            profile_picture=updated.profile_picture,
            bio=updated.bio,
            gender=updated.gender,
            birth_date=updated.birth_date.isoformat() if updated.birth_date else None,
            country=updated.country,
            city=updated.city,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )
    except Exception as e:
        log_error(f"Error updating bio {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/gender", response_model=UserProfileOut)
async def update_my_gender(
    payload: GenderUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        use_case = UpdateGenderUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.gender)
        return UserProfileOut(
            id=str(updated.id),
            username=updated.username,
            email=updated.email,
            profile_picture=updated.profile_picture,
            bio=updated.bio,
            gender=updated.gender,
            birth_date=updated.birth_date.isoformat() if updated.birth_date else None,
            country=updated.country,
            city=updated.city,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Error updating gender {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/birth-date", response_model=UserProfileOut)
async def update_my_birth_date(
    payload: BirthDateUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        use_case = UpdateBirthDateUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.birth_date)
        return UserProfileOut(
            id=str(updated.id),
            username=updated.username,
            email=updated.email,
            profile_picture=updated.profile_picture,
            bio=updated.bio,
            gender=updated.gender,
            birth_date=updated.birth_date.isoformat() if updated.birth_date else None,
            country=updated.country,
            city=updated.city,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )
    except Exception as e:
        log_error(f"Error updating birth date {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/location", response_model=UserProfileOut)
async def update_my_location(
    payload: LocationUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        use_case = UpdateLocationUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.country, payload.city)
        return UserProfileOut(
            id=str(updated.id),
            username=updated.username,
            email=updated.email,
            profile_picture=updated.profile_picture,
            bio=updated.bio,
            gender=updated.gender,
            birth_date=updated.birth_date.isoformat() if updated.birth_date else None,
            country=updated.country,
            city=updated.city,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )
    except Exception as e:
        log_error(f"Error updating location {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Internal server error")