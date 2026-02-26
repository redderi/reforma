

from uuid import UUID

from pydantic import BaseModel


class PresignRequest(BaseModel):
    type: str  # "avatar", "template", "survey_image", "report"
    user_id: UUID | None = None
    owner_id: UUID | None = None
    template_id: UUID | None = None
    survey_id: UUID | None = None
    question_id: UUID | None = None
    report_id: UUID | None = None
    filename: str
    content_type: str
    file_format: str | None = None


class PresignResponse(BaseModel):
    object_key: str
    upload_url: str


class FileInfo(BaseModel):
    object_key: str
    type: str
    presigned_url: str
    file_format: str | None = None


class ConfirmUploadRequest(BaseModel):
    object_key: str
    file_type: str
    owner_id: UUID | None = None
    template_id: UUID | None = None
    survey_id: UUID | None = None
    question_id: UUID | None = None
    report_id: UUID | None = None
    file_format: str | None = None