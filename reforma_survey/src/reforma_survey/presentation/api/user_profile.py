from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from reforma_survey.presentation.schemas.user_profile_schema import (
    BioUpdate,
    BirthDateUpdate,
    GenderUpdate,
    LocationUpdate,
    ProfilePictureUpdate,
    UserProfileOut,
)
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.infrastructure.repositories.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from reforma_survey.application.user_profile.get_user_profile_by_id_use_case import (
    GetUserProfileByIdUseCase,
)
from reforma_survey.application.user_profile.update_profile_picture_use_case import (
    UpdateProfilePictureUseCase,
)
from reforma_survey.application.user_profile.update_bio_use_case import UpdateBioUseCase
from reforma_survey.application.user_profile.update_gender_use_case import (
    UpdateGenderUseCase,
)
from reforma_survey.application.user_profile.update_birth_date_use_case import (
    UpdateBirthDateUseCase,
)
from reforma_survey.application.user_profile.update_location_use_case import (
    UpdateLocationUseCase,
)
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", response_model=UserProfileOut)
async def get_my_profile(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve current user profile",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
    )

    try:
        use_case = GetUserProfileByIdUseCase(UserProfileRepositoryImpl(db))
        profile = await use_case.execute(current_user_id)

        if not profile:
            log_warning(
                "User profile not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
            )
            raise HTTPException(status_code=404, detail="Profile not found")

        log_info(
            "User profile retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=profile.balance,
            surveys=[str(s) for s in profile.surveys],
            templates=[str(t) for t in profile.templates],
            reports=[str(r) for r in profile.reports],
            responses=[r.id for r in profile.responses],
        )

    except Exception as e:
        log_error(
            "Unexpected error retrieving user profile",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/profile-picture", response_model=UserProfileOut)
async def update_my_profile_picture(
    request: Request,
    payload: ProfilePictureUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update profile picture attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "new_picture_url": payload.picture_url[:100] + "..."
            if payload.picture_url
            else None
        },
    )

    try:
        use_case = UpdateProfilePictureUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.picture_url)

        log_info(
            "Profile picture updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=updated.balance,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except Exception as e:
        log_error(
            "Unexpected error updating profile picture",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/bio", response_model=UserProfileOut)
async def update_my_bio(
    request: Request,
    payload: BioUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update bio attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"new_bio_length": len(payload.bio) if payload.bio else 0},
    )

    try:
        use_case = UpdateBioUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.bio)

        log_info(
            "Bio updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=updated.balance,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except Exception as e:
        log_error(
            "Unexpected error updating bio",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/gender", response_model=UserProfileOut)
async def update_my_gender(
    request: Request,
    payload: GenderUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update gender attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"new_gender": payload.gender},
    )

    try:
        use_case = UpdateGenderUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.gender)

        log_info(
            "Gender updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=updated.balance,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except ValueError as e:
        log_warning(
            "Gender update failed due to validation error",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating gender",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/birth-date", response_model=UserProfileOut)
async def update_my_birth_date(
    request: Request,
    payload: BirthDateUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update birth date attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "new_birth_date": payload.birth_date.isoformat()
            if payload.birth_date
            else None
        },
    )

    try:
        use_case = UpdateBirthDateUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.birth_date)

        log_info(
            "Birth date updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=updated.balance,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except Exception as e:
        log_error(
            "Unexpected error updating birth date",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/location", response_model=UserProfileOut)
async def update_my_location(
    request: Request,
    payload: LocationUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update location attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"new_country": payload.country, "new_city": payload.city},
    )

    try:
        use_case = UpdateLocationUseCase(UserProfileRepositoryImpl(db))
        updated = await use_case.execute(current_user_id, payload.country, payload.city)

        log_info(
            "Location updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
        )

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
            balance=updated.balance,
            surveys=[str(s) for s in updated.surveys],
            templates=[str(t) for t in updated.templates],
            reports=[str(r) for r in updated.reports],
        )

    except Exception as e:
        log_error(
            "Unexpected error updating location",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
