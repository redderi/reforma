from abc import ABC, abstractmethod


class BaseStorageClient(ABC):
    @abstractmethod
    async def upload_fileobj(self, file_obj, object_name: str) -> str:
        pass

    @abstractmethod
    async def generate_presigned_url(
        self, object_name: str, expires_in: int = 604800
    ) -> str:
        pass

    @abstractmethod
    async def delete_object(self, object_name: str) -> None:
        pass

    @abstractmethod
    async def object_exists(self, object_name: str) -> bool:
        pass
