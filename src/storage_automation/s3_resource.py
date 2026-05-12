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
        self.s3_resource = boto3.resource( # Same customization as the client so MinIO behaves the same for both.
            "s3",
            endpoint_url=Settings.s3_endpoint_url,
            aws_access_key_id=Settings.aws_access_key_id,
            aws_secret_access_key=Settings.aws_secret_access_key,
            region_name=Settings.aws_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = self.s3_resource.Bucket(self.bucket_name) # handle bucket for resource-style calls.

    @property
    def get_access_type(self) -> str:
        return "S3 Resource"

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            self.s3_resource.meta.client.head_bucket(Bucket=bucket_name)
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

            if Settings.aws_region and Settings.aws_region != "us-east-1":
                create_bucket_args["CreateBucketConfiguration"] = {
                    "LocationConstraint": Settings.aws_region
                }

            self.s3_resource.create_bucket(**create_bucket_args)
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
            bucket = self.s3_resource.Bucket(bucket_name)
            versioning_status = self.s3_resource.BucketVersioning(bucket_name).status

            logger.info("Emptying bucket before deletion.")
            if versioning_status in {"Enabled", "Suspended"}:
                bucket.object_versions.delete()
            else:
                bucket.objects.all().delete() # Clearing the bucket before deletion for resource calls.

            logger.info("Bucket is empty, let's delete it.")
            bucket.delete()

            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket deletion failed: {error}")
            return {"message": "Bucket deletion failed"}

    def list_buckets(self) -> dict:
        try:
            return self.s3_resource.meta.client.list_buckets()
        except ClientError as error:
            logger.error(f"Bucket listing failed: {error}")
            return {"message": "Bucket listing failed"}

    def list_objects(self, bucket_name: str) -> list[dict]:
        try:
            objects = self.s3_resource.Bucket(bucket_name).objects.all()
            return [
                {
                    "key": item.key,
                    "size": item.size,
                    "last_modified": item.last_modified.isoformat(),
                }
            for item in objects
            ]
        except ClientError as error:
            logger.error(f"Objects listing failed: {error}")
            return []

    def get_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        try:
            return self.s3_resource.meta.client.head_object(Bucket=bucket_name, Key=object_key)
        except ClientError as error:
            logger.error(f"Object metadata retrieval failed: {error}")
            return {"message": "Object metadata retrieval failed"}

    def get_object_size(self, bucket_name: str, object_key: str) -> int:
        try:
            return self.s3_resource.meta.client.head_object(Bucket=bucket_name, Key=object_key)["ContentLength"]
        except ClientError as error:
            logger.error(f"Object size retrieval failed: {error}")
            return -1

    def write_object(self, bucket_name: str, object_key: str, content: bytes) -> dict:
        try:
            self.ensure_bucket_exists(bucket_name)
            self.s3_resource.Object(bucket_name, object_key).put(Body=content)
            return {"message": "Object written successfully"}
        except (ClientError, RuntimeError) as error:
            logger.error(f"Object writing failed: {error}")
            return {"message": "Object writing failed"}

    def read_object(self, bucket_name: str, object_key: str) -> bytes | dict:
        try:
            return self.s3_resource.Object(bucket_name, object_key).get()["Body"].read()
        except ClientError as error:
            logger.error(f"Object reading failed: {error}")
            return {"message": "Object reading failed"}

    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        try:
            self.s3_resource.Object(bucket_name, object_key).delete()
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
            self.s3_resource.Bucket(bucket_name).upload_file(file_path, object_key)
            return {"message": "Object uploaded successfully"}
        except (ClientError, RuntimeError, OSError) as error:
            logger.error(f"Object upload failed: {error}")
            return {"message": "Object upload failed"}

    def download_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        try:
            self.s3_resource.Bucket(bucket_name).download_file(object_key, file_path)
            return {"message": "Object downloaded successfully"}
        except (ClientError, OSError) as error:
            logger.error(f"Object download failed: {error}")
            return {"message": "Object download failed"}

