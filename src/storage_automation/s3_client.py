from io import BytesIO

import boto3
from src.storage_automation.interfaces.s3 import S3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.storage_api.settings import settings
import logging

logger = logging.getLogger(__name__)

class S3Client(S3):

    def __init__(self) -> None:
        self.bucket_name = settings.minio_bucket_name
        self.s3_client = boto3.client( # customizing how the S3 client talks to the MinIO service.
            "s3", # AWS service identifier, 's3' as the low-level client to build.
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4"), # signing S3 API calls with AWS Signature Ver 4.
        )

    @property
    def get_access_type(self) -> str:
        return "S3 Client"

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code", "")

            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                logger.error(f"Problem checking whether {bucket_name} bucket exists: {error}")
                raise

            logger.warning(f"Bucket does not exist: {bucket_name}. Creating bucket...")
            result = self.create_bucket(bucket_name)

            if result.get("message") != "Bucket created successfully":
                raise RuntimeError(result.get("error") or f"Failed to create bucket: {bucket_name}")

    def create_bucket(self, bucket_name: str) -> dict:
        try:
            create_bucket_args = {"Bucket": bucket_name}

            if settings.aws_region and settings.aws_region != "us-east-1":
                create_bucket_args["CreateBucketConfiguration"] = {
                    "LocationConstraint": settings.aws_region
                }

            self.s3_client.create_bucket(**create_bucket_args)
            return {"message": "Bucket created successfully"}
        except ClientError as error:
            logger.error(f"Bucket creation failed: {error}")
            return {
                "message": "Bucket creation failed",
                "bucket_name": bucket_name,
                "error": str(error),
            }

    def delete_bucket(self, bucket_name: str) -> dict:
        try:
            self.s3_client.delete_bucket(Bucket=bucket_name)
            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket deletion failed: {bucket_name}")
            return {"message": "Bucket deletion failed"}

    def list_buckets(self) -> dict:
        try:
            return self.s3_client.list_buckets()
        except ClientError as error:
            logger.error(f"Bucket listing failed: {error}")
            return {"message": "Bucket listing failed"}

    def list_objects(self, bucket_name: str) -> list[dict]:
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = response.get("Contents", [])
            return [
                {
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat(),
                }
            for item in objects
            ]
        except ClientError as error:
            logger.error(f"Objects listing failed: {error}")
            return []

    def get_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        try:
            return self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
        except ClientError as error:
            logger.error(f"Object metadata retrieval failed: {error}")
            return {"message": "Object metadata retrieval failed"}

    def get_object_size(self, bucket_name: str, object_key: str) -> int:
        try:
            return self.s3_client.head_object(Bucket=bucket_name, Key=object_key)["ContentLength"]
        except ClientError as error:
            logger.error(f"Object size retrieval failed: {error}")
            return -1

    def write_object(self, bucket_name: str, object_key: str, content: bytes) -> dict:
        try:
            self.ensure_bucket_exists(bucket_name)
            self.s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=content)
            return {"message": "Object written successfully"}
        except (ClientError, RuntimeError) as error:
            logger.error(f"Object writing failed: {error}")
            return {"message": "Object writing failed"}

    def read_object(self, bucket_name: str, object_key: str) -> bytes | dict:
        try:
            return self.s3_client.get_object(Bucket=bucket_name, Key=object_key)["Body"].read()
        except ClientError as error:
            logger.error(f"Object reading failed: {error}")
            return {"message": "Object reading failed"}

    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            return {"message": "Object deleted successfully",
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                    }
        except ClientError as error:
            logger.error(f"Object deletion failed: {error}")
            return {"message": "Object deletion failed"}

    def upload_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        try:
            self.ensure_bucket_exists(bucket_name)
            self.s3_client.upload_file(file_path, bucket_name, object_key)
            return {"message": "Object uploaded successfully"}
        except (ClientError, RuntimeError, OSError) as error:
            logger.error(f"Object upload failed: {error}")
            return {"message": "Object upload failed"}

    def download_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        try:
            self.s3_client.download_file(bucket_name, object_key, file_path)
            return {"message": "Object downloaded successfully"}
        except (ClientError, OSError) as error:
            logger.error(f"Object download failed: {error}")
            return {"message": "Object download failed"}

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> dict:
        """
        Upload in-memory bytes to the configured default bucket (put_object).
        Typical use: FastAPI after await upload_file.read().
        """
        try:
            self.ensure_bucket_exists(self.bucket_name)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type,
            )
            return {
                "bucket": self.bucket_name,
                "object_key": object_key,
                "content_type": content_type,
                "message": "Object uploaded successfully",
            }
        except (ClientError, RuntimeError) as error:
            logger.error(f"Object upload failed: {error}")
            return {"message": "Object upload failed"}

    def download_file(self, object_key: str) -> tuple[BytesIO, str]:
        """
        Return object body as BytesIO and Content-Type (default bucket).
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            body = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")
            return BytesIO(body), content_type
        except ClientError as error:
            logger.error(f"Object download failed: {error}")
            raise
