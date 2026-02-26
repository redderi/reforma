from uuid import UUID
from pathlib import Path


def user_avatar_key(user_id: UUID, filename: str) -> str:
    ext = Path(filename).suffix
    return f"users/{user_id}/avatar{ext}"


def template_asset_key(
    owner_id: UUID,
    template_id: UUID,
    filename: str,
) -> str:
    safe_name = Path(filename).name
    return f"templates/{owner_id}/{template_id}/{safe_name}"


def survey_question_image_key(
    survey_id: UUID,
    question_id: UUID,
    filename: str,
) -> str:
    safe_name = Path(filename).name
    return f"surveys/{survey_id}/questions/{question_id}/{safe_name}"


def report_file_key(
    survey_id: UUID,
    report_id: UUID,
    file_format: str,
) -> str:
    return f"surveys/{survey_id}/reports/{report_id}.{file_format.lower()}"
