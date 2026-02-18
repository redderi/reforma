import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional

from reforma_survey.infrastructure.config.storage_config import (
    STORAGE_ENDPOINT,
    STORAGE_ACCESS_KEY,
    STORAGE_SECRET_KEY,
    STORAGE_BUCKET,
    STORAGE_SIGNATURE_VERSION,
    STORAGE_REGION_NAME
)
from reforma_survey.infrastructure.storage.base_storage_client import BaseStorageClient
from reforma_common.logger import log_info, log_warning, log_error


class S3StorageClient(BaseStorageClient):

    def __init__(self):
        self.client = boto3.client(
            service_name='s3',
            endpoint_url=STORAGE_ENDPOINT,
            aws_access_key_id=STORAGE_ACCESS_KEY,
            aws_secret_access_key=STORAGE_SECRET_KEY,
            region_name=STORAGE_REGION_NAME or None,
            config=Config(
                signature_version=STORAGE_SIGNATURE_VERSION,
                retries={'max_attempts': 3, 'mode': 'standard'}
            ),
            verify=False  # for dev
        )
        self.bucket = STORAGE_BUCKET

        log_info(
            f"S3StorageClient инициализирован | endpoint={STORAGE_ENDPOINT} | bucket={self.bucket}",
            service="report-service"
        )

    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:

        try:
            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket,
                Key=object_name
            )
            log_info(f"Файл успешно загружен: {object_name}", service="report-service")
            return object_name
        except ClientError as e:
            log_error(f"Ошибка загрузки файла {object_name}: {e}", service="report-service")
            raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}")

    async def generate_presigned_url(self, object_name: str, expires_in: int = 604800) -> str:

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': object_name
                },
                ExpiresIn=expires_in
            )
            log_info(
                f"Сгенерирована presigned-ссылка: {object_name} (TTL: {expires_in} сек)",
                service="report-service"
            )
            return url
        except ClientError as e:
            log_error(f"Ошибка генерации presigned-ссылки для {object_name}: {e}", service="report-service")
            raise RuntimeError(f"Не удалось сгенерировать ссылку: {str(e)}")

    async def delete_object(self, object_name: str) -> None:

        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_name)
            log_info(f"Объект успешно удалён: {object_name}", service="report-service")
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                log_warning(f"Объект {object_name} уже не существует", service="report-service")
            else:
                log_error(f"Ошибка удаления объекта {object_name}: {e}", service="report-service")

    async def object_exists(self, object_name: str) -> bool:

        try:
            self.client.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            log_error(f"Ошибка проверки объекта {object_name}: {e}", service="report-service")
            raise
