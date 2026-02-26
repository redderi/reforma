from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from typing import Optional, List
import io
import asyncio
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.schemas.storage import (
    ConfirmUploadRequest,
    FileInfo,
    PresignRequest,
    PresignResponse,
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from reforma_survey.infrastructure.storage.s3_client import S3StorageClient
from reforma_survey.infrastructure.storage.get_storage_key import (
    user_avatar_key,
    template_asset_key,
    survey_question_image_key,
    report_file_key,
)

from reforma_survey.infrastructure.db.models import FileModel

storage = S3StorageClient()

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.post("/uploads/presign", response_model=PresignResponse)
async def presign_upload(req: PresignRequest):
    try:
        if req.type == "avatar":
            if not req.user_id:
                raise HTTPException(400, "user_id обязателен для аватара")
            key = user_avatar_key(req.user_id, req.filename)

        elif req.type == "template":
            if not (req.owner_id and req.template_id):
                raise HTTPException(
                    400, "owner_id и template_id обязательны для шаблона"
                )
            key = template_asset_key(req.owner_id, req.template_id, req.filename)

        elif req.type == "survey_image":
            if not (req.survey_id and req.question_id):
                raise HTTPException(
                    400, "survey_id и question_id обязательны для изображения вопроса"
                )
            key = survey_question_image_key(
                req.survey_id, req.question_id, req.filename
            )

        elif req.type == "report":
            if not (req.survey_id and req.report_id and req.file_format):
                raise HTTPException(
                    400, "survey_id, report_id и file_format обязательны для отчёта"
                )
            key = report_file_key(req.survey_id, req.report_id, req.file_format)

        else:
            raise HTTPException(400, "Неверный тип файла")

        url = await storage.generate_presigned_put_url(
            object_name=key, content_type=req.content_type, expires_in=600
        )

        return PresignResponse(object_key=key, upload_url=url)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ошибка генерации presigned URL: {str(e)}")


@router.post("/uploads/confirm")
async def confirm_upload(
    data: ConfirmUploadRequest,
    db: AsyncSession = Depends(get_db),
):
    exists = await storage.object_exists(data.object_key)
    if not exists:
        raise HTTPException(404, "Файл не найден в хранилище")

    stmt = (
        insert(FileModel)
        .values(
            object_key=data.object_key,
            type=data.file_type,
            owner_id=data.owner_id,
            template_id=data.template_id,
            survey_id=data.survey_id,
            question_id=data.question_id,
            report_id=data.report_id,
            file_format=data.file_format,
        )
        .on_conflict_do_nothing(index_elements=["object_key"])
    )

    await db.execute(stmt)
    await db.commit()

    return {"status": "confirmed", "object_key": data.object_key}


@router.get("/uploads/list", response_model=List[FileInfo])
async def list_files(
    file_type: Optional[str] = Query(None),
    owner_id: Optional[UUID] = Query(None),
    survey_id: Optional[UUID] = Query(None),
    template_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FileModel)

    if file_type:
        stmt = stmt.where(FileModel.type == file_type)
    if owner_id:
        stmt = stmt.where(FileModel.owner_id == owner_id)
    if survey_id:
        stmt = stmt.where(FileModel.survey_id == survey_id)
    if template_id:
        stmt = stmt.where(FileModel.template_id == template_id)

    result = await db.execute(stmt)
    db_files = result.scalars().all()

    files: List[FileInfo] = []

    for f in db_files:
        try:
            url = await storage.generate_presigned_url(f.object_key, expires_in=3600)
            files.append(
                FileInfo(
                    object_key=f.object_key,
                    type=f.type or "unknown",
                    presigned_url=url,
                    file_format=f.file_format,
                )
            )
        except Exception:
            continue

    return files


@router.get("/uploads/download/{object_key:path}")
async def download_file(object_key: str, user_id: Optional[UUID] = Query(None)):
    # Здесь можно добавить более строгую проверку прав через БД
    # Пока оставляем простую проверку по пути
    if not object_key.startswith("users/"):
        if not user_id or f"/{user_id}/" not in object_key:
            raise HTTPException(403, "Нет доступа к файлу")

    try:
        loop = asyncio.get_running_loop()
        obj = await loop.run_in_executor(
            None,
            lambda: storage.client.get_object(Bucket=storage.bucket, Key=object_key),
        )

        filename = object_key.split("/")[-1] or "file"

        return StreamingResponse(
            io.BytesIO(obj["Body"].read()),
            media_type=obj.get("ContentType", "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(500, f"Ошибка скачивания: {str(e)}")


@router.delete("/uploads/delete/{object_key:path}")
async def delete_file(
    object_key: str,
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if not object_key.startswith("users/"):
        if not user_id or f"/{user_id}/" not in object_key:
            raise HTTPException(403, "Нет доступа для удаления")

    await storage.delete_object(object_key)

    stmt = delete(FileModel).where(FileModel.object_key == object_key)
    await db.execute(stmt)
    await db.commit()

    return {"status": "deleted", "object_key": object_key}
