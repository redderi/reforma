import asyncio
from typing import BinaryIO
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from reforma_survey.infrastructure.config.storage_config import (
    STORAGE_ENDPOINT,
    STORAGE_PUBLIC_ENDPOINT,
    STORAGE_ACCESS_KEY,
    STORAGE_SECRET_KEY,
    STORAGE_BUCKET,
    STORAGE_SIGNATURE_VERSION,
    STORAGE_REGION_NAME,
)
from reforma_survey.infrastructure.storage.base_storage_client import BaseStorageClient


class S3StorageClient(BaseStorageClient):
    def __init__(self):
        self.internal_endpoint = STORAGE_ENDPOINT
        self.public_endpoint = STORAGE_PUBLIC_ENDPOINT

        self.internal_netloc = self.internal_endpoint.split("://", 1)[-1].rstrip("/")
        self.public_netloc = self.public_endpoint.split("://", 1)[-1].rstrip("/")

        self.bucket = STORAGE_BUCKET

        self.client = boto3.client(
            service_name="s3",
            endpoint_url=self.internal_endpoint,
            aws_access_key_id=STORAGE_ACCESS_KEY,
            aws_secret_access_key=STORAGE_SECRET_KEY,
            region_name=STORAGE_REGION_NAME,
            config=Config(
                signature_version=STORAGE_SIGNATURE_VERSION,
                retries={"max_attempts": 5, "mode": "standard"},
                connect_timeout=10,
                read_timeout=30,
            ),
            verify=False,  # dev
        )

    def _make_public_url(self, url: str) -> str:
        if self.internal_netloc in url:
            url = url.replace(self.internal_netloc, self.public_netloc)
        return url

    async def upload_fileobj(self, file_obj: BinaryIO, object_name: str) -> str:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.client.upload_fileobj(
                    Fileobj=file_obj,
                    Bucket=self.bucket,
                    Key=object_name,
                ),
            )
            return object_name
        except ClientError as e:
            raise RuntimeError(
                f"File download error {object_name}: {e.response['Error']['Message']}"
            )


    async def generate_presigned_url(
        self,
        object_name: str,
        expires_in: int = 604800,  
    ) -> str:
        loop = asyncio.get_running_loop()
        try:
            url = await loop.run_in_executor(
                None,
                lambda: self.client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket, "Key": object_name},
                    ExpiresIn=expires_in,
                    HttpMethod="GET",
                ),
            )
            return self._make_public_url(url)
        except ClientError as e:
            raise RuntimeError(
                f"Failed to create presigned GET URL for {object_name}: {str(e)}"
            )

    async def generate_presigned_put_url(
        self,
        object_name: str,
        content_type: str,
        expires_in: int = 600, 
    ) -> str:
        loop = asyncio.get_running_loop()
        try:
            url = await loop.run_in_executor(
                None,
                lambda: self.client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": object_name,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires_in,
                    HttpMethod="PUT",
                ),
            )
            return self._make_public_url(url)
        except ClientError as e:
            raise RuntimeError(
                f"Failed to create presigned PUT URL for {object_name}: {str(e)}"
            )

    async def delete_object(self, object_name: str) -> None:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_object(
                    Bucket=self.bucket,
                    Key=object_name,
                ),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                raise RuntimeError(
                    f"Delete error {object_name}: {e.response['Error']['Message']}"
                )

    async def object_exists(self, object_name: str) -> bool:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.client.head_object(
                    Bucket=self.bucket,
                    Key=object_name,
                ),
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise RuntimeError(f"Ошибка head-запроса к {object_name}: {str(e)}")
