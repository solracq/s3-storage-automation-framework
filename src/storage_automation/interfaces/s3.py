from abc import ABC, abstractmethod

class S3(ABC):

    @property
    @abstractmethod
    def access_type(self):
        pass

    @abstractmethod
    def bucket_exists(self, bucket_name:str) -> bool:
        pass

    @abstractmethod
    def create_bucket(self, bucket_name: str) -> dict:
        pass

    @abstractmethod
    def delete_bucket(self, bucket_name: str) -> dict:
        pass

    @abstractmethod
    def list_buckets(self) -> dict:
        pass

    @abstractmethod
    def list_objects(self, bucket_name: str) -> dict:
        pass

    @abstractmethod
    def get_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        pass

    @abstractmethod
    def get_object_size(self, bucket_name: str, object_key: str) -> dict:
        pass

    @abstractmethod
    def write_object(self, bucket_name: str, object_key: str, content: bytes) -> dict:
        pass

    @abstractmethod
    def read_object(self, bucket_name: str, object_key: str) -> dict:
        pass
    
    @abstractmethod
    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        pass

    @abstractmethod
    def upload_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        pass

    @abstractmethod
    def download_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        pass
