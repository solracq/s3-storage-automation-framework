import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from src.storage_automation.interfaces.s3 import S3
from app.storage_api.settings import Settings
import logging

logger = logging.getLogger(__name__)

class S3Resource(S3):
    def __init__(self) -> None:
        self.bucket_name = Settings.minio_bucket_name
        self.s3_resource = boto3.resource( # Same customization as the client so MinIO behaves teh same for both.
            "s3",
            endpoint_url=Settings.s3_endpoint_url,
            aws_access_key_id=Settings.aws_access_key_id,
            aws_secret_access_key=Settings.aws_secret_access_key,
            region_name=Settings.aws_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = self.s3_resource.Bucket(self.bucket_name) # handle bucket for resurce-style calls.

    @property
    def access_type(self):
        return "S3 Resource"

    def bucket_exist(self, bucket_name: str) -> bool:
        try:
            self.s3_resource.Bucket(bucket_name).exists()
            return True
        except ClientError as error:
            logger.error(f"Bucket does not exist: {bucket_name}")
            return False

    def create_bucket(self, bucket_name: str) -> dict:
        try:
            self.s3_resource.create_bucket(Bucket=self.bucket)
            return {"message": "Bucket created successfully"}
        except ClientError as error:
            logger.error(f"Bucket creation failed: {error}")
            return {"message": "Bucket creation failed"}

    def delete_bucket(self, bucket_name: str) -> dict:
        try:
            self.s3_resource.delete_bucket(Bucket=self.bucket)
            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket deletion failed: {error}")
            return {"message": "Bucket deletion failed"}

    def list_buckets(self) -> dict:
        try:
            return self.s3_resource.buckets.all()
        except ClientError as error:
            logger.error(f"Bucket listing failed: {error}")
            return {"message": "Bucket listing failed"}

    def list_objects(self, bucket_name: str) -> dict:
        try:
            return self.bucket.objects.all()
            return {"message": "Objects listed successfully"}
        except ClientError as error:
            logger.error(f"Objects listing failed: {error}")
            return {"message": "Objects listing failed"}   

    def get_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        try:
            return self.bucket.objects.filter(Prefix=object_key).first().metadata
        except ClientError as error:
            logger.error(f"Object metadata retrieval failed: {error}")
            return {"message": "Object metadata retrieval failed"}

    def get_object_size(self, bucket_name: str, object_key: str) -> dict:
        try:
            return self.bucket.objects.filter(Prefix=object_key).first().size
        except ClientError as error:
            logger.error(f"Object size retrieval failed: {error}")
            return {"message": "Object size retrieval failed"}

    def write_object(self, bucket_name: str, object_key: str, content: bytes) -> dict:
        try:
            self.bucket.objects.filter(Prefix=object_key).write(content)
            return {"message": "Object written successfully"}
        except ClientError as error:
            logger.error(f"Object writing failed: {error}")
            return {"message": "Object writing failed"}

    def read_object(self, bucket_name: str, object_key: str) -> dict:
        try:
            return self.bucket.objects.filter(Prefix=object_key).first().read()
        except ClientError as error:
            logger.error(f"Object reading failed: {error}")
            return {"message": "Object reading failed"}

    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        try:
            self.bucket.objects.filter(Prefix=object_key).delete()
            return {"message": "Object deleted successfully"}
        except ClientError as error:
            logger.error(f"Object deletion failed: {error}")
            return {"message": "Object deletion failed"}

    def upload_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        try:
            self.bucket.upload_file(file_path, object_key)
            return {"message": "Object uploaded successfully"}
        except ClientError as error:
            logger.error(f"Object upload failed: {error}")
            return {"message": "Object upload failed"}

    def download_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        try:
            self.bucket.download_file(object_key, file_path)
            return {"message": "Object downloaded successfully"}
        except ClientError as error:
            logger.error(f"Object download failed: {error}")
            return {"message": "Object download failed"}
