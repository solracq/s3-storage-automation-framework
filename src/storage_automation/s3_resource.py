"""
Higher-level S3 access implementation built on top of ``boto3.resource("s3")``.

This module uses boto3's object-oriented resource layer, where buckets and
objects are represented as Python objects and collections. It is useful for
tests that prefer more readable, high-level interactions while still allowing
fall back to ``meta.client`` when a lower-level S3 response shape is needed.
"""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from src.storage_automation.interfaces.s3 import S3
from app.storage_api.settings import settings
import logging

logger = logging.getLogger(__name__)

class S3Resource(S3):
    """
    High-level S3 wrapper that uses resource-style calls.

    The boto3 resource API exposes abstractions such as ``Bucket`` and
    ``Object`` and supports object collections, which can make storage tests
    easier to read. This class complements ``S3Client`` by demonstrating the
    higher-level SDK access pattern against the same MinIO backend.
    """

    def __init__(self) -> None:
        """
        Initialize the S3 resource with MinIO/S3-compatible configuration.
        """
        self.bucket_name = settings.minio_bucket_name
        self.s3_resource = boto3.resource( # Same customization as the client so MinIO behaves the same for both.
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = self.s3_resource.Bucket(self.bucket_name) # handle bucket for resource-style calls.

    @property
    def get_access_type(self) -> str:
        """
        Return the storage access implementation name.

        Args:
            None
        Returns:
            str: Human-readable access type label.
        Raises:
            None
        """
        return "S3 Resource"

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """
        Ensure a bucket exists, creating it when it is missing.

        Args:
            bucket_name (str): Name of the bucket to verify.
        Returns:
            None
        Raises:
            ClientError: If the bucket check fails for a reason other than not found.
            RuntimeError: If bucket creation is attempted but does not succeed.
        """
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
        """
        Create a bucket in the configured S3-compatible storage.

        Args:
            bucket_name (str): Name of the bucket to create.
        Returns:
            dict: Success or failure details for the create operation.
        Raises:
            None
        """
        try:
            create_bucket_args = {"Bucket": bucket_name}

            if settings.aws_region and settings.aws_region != "us-east-1":
                create_bucket_args["CreateBucketConfiguration"] = {
                    "LocationConstraint": settings.aws_region
                }
            logger.info("Creating bucket.")
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
        """
        Delete a bucket from the configured S3 storage.

        Args:
            bucket_name (str): Name of the bucket to delete.
        Returns:
            dict: Success or failure details for the delete operation.
        Raises:
            None
        """
        try:
            bucket = self.s3_resource.Bucket(bucket_name)
            logger.info("Deleting bucket.")
            bucket.delete()
            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket deletion failed: {error}")
            return {"message": "Bucket deletion failed"}
    
    def delete_bucket_recursive(self, bucket_name: str) -> dict:
        """
        Delete a bucket after removing its contents.

        Args:
            bucket_name (str): Name of the bucket to delete.
        Returns:
            dict: Success or failure details for the delete operation.
        Raises:
            None
        """
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
            logger.error(f"Bucket recursive deletion failed: {error}")
            return {"message": "Bucket deletion failed"}

    def list_buckets(self) -> dict:
        """
        List all buckets available to the configured resource client.

        Args:
            None
        Returns:
            dict: Raw bucket listing response or a failure message.
        Raises:
            None
        """
        try:
            logger.info("Listing buckets.")
            return self.s3_resource.meta.client.list_buckets()
        except ClientError as error:
            logger.error(f"Bucket listing failed: {error}")
            return {"message": "Bucket listing failed"}

    def list_objects(self, bucket_name: str) -> list[dict]:
        """
        List objects stored in a bucket.

        Args:
            bucket_name (str): Name of the bucket to inspect.
        Returns:
            list[dict]: Object summaries including key, size, and last modified date.
        Raises:
            None
        """
        try:
            logger.info("Listing objects.")
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
        """
        Retrieve metadata for an object stored in a bucket.

        Args:
            bucket_name (str): Name of the bucket containing the object.
            object_key (str): Key of the object to inspect.
        Returns:
            dict: Metadata response for the object or a failure message.
        Raises:
            None
        """
        try:
            logger.info("Retrieving object metadata.")
            return self.s3_resource.meta.client.head_object(Bucket=bucket_name, Key=object_key)
        except ClientError as error:
            logger.error(f"Object metadata retrieval failed: {error}")
            return {"message": "Object metadata retrieval failed"}

    def get_object_size(self, bucket_name: str, object_key: str) -> int:
        """
        Get the size of an object in bytes.

        Args:
            bucket_name (str): Name of the bucket containing the object.
            object_key (str): Key of the object to inspect.
        Returns:
            int: Object size in bytes, or `-1` on failure.
        Raises:
            None
        """
        try:
            logger.info("Retrieving object size.")
            return self.s3_resource.meta.client.head_object(Bucket=bucket_name, Key=object_key)["ContentLength"]
        except ClientError as error:
            logger.error(f"Object size retrieval failed: {error}")
            return -1

    def write_object(self, bucket_name: str, object_key: str, content: bytes) -> dict:
        """
        Write raw bytes to an object key in a bucket.

        Args:
            bucket_name (str): Name of the target bucket.
            object_key (str): Key to create or overwrite.
            content (bytes): Raw object content to store.
        Returns:
            dict: Success or failure details for the write operation.
        Raises:
            None
        """
        try:
            self.ensure_bucket_exists(bucket_name)
            logger.info("Writing on object.")
            self.s3_resource.Object(bucket_name, object_key).put(Body=content)
            return {"message": "Object written successfully"}
        except (ClientError, RuntimeError) as error:
            logger.error(f"Object writing failed: {error}")
            return {"message": "Object writing failed"}

    def read_object(self, bucket_name: str, object_key: str) -> bytes | dict:
        """
        Read the full content of an object from a bucket.

        Args:
            bucket_name (str): Name of the bucket containing the object.
            object_key (str): Key of the object to read.
        Returns:
            bytes | dict: Raw object bytes on success, otherwise a failure message.
        Raises:
            None
        """
        try:
            logger.info("Reading object.")
            return self.s3_resource.Object(bucket_name, object_key).get()["Body"].read()
        except ClientError as error:
            logger.error(f"Object reading failed: {error}")
            return {"message": "Object reading failed"}

    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        """
        Delete an object from a bucket.

        Args:
            bucket_name (str): Name of the bucket containing the object.
            object_key (str): Key of the object to delete.
        Returns:
            dict: Success or failure details for the delete operation.
        Raises:
            None
        """
        try:
            logger.info("Deleting object.")
            self.s3_resource.Object(bucket_name, object_key).delete()
            return {"message": "Object deleted successfully",
                    "bucket_name": bucket_name,
                    "object_key": object_key,
                    }
        except ClientError as error:
            logger.error(f"Object deletion failed: {error}")
            return {"message": "Object deletion failed"}

    def upload_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        """
        Upload a local file into a bucket using the provided object key.

        Args:
            bucket_name (str): Name of the target bucket.
            object_key (str): Key to assign to the uploaded object.
            file_path (str): Path to the local file to upload.
        Returns:
            dict: Success or failure details for the upload operation.
        Raises:
            None
        """
        try:
            self.ensure_bucket_exists(bucket_name)
            logger.info(f"Uploading object to {bucket_name}.")
            self.s3_resource.Bucket(bucket_name).upload_file(file_path, object_key)
            return {"message": "Object uploaded successfully"}
        except (ClientError, RuntimeError, OSError) as error:
            logger.error(f"Object upload failed: {error}")
            return {"message": "Object upload failed"}

    def download_object(self, bucket_name: str, object_key: str, file_path: str) -> dict:
        """
        Download an object from a bucket to a local file path.

        Args:
            bucket_name (str): Name of the bucket containing the object.
            object_key (str): Key of the object to download.
            file_path (str): Local destination path for the downloaded file.
        Returns:
            dict: Success or failure details for the download operation.
        Raises:
            None
        """
        try:
            logger.info(f"Downloading object '{file_path}' from {bucket_name}.")
            self.s3_resource.Bucket(bucket_name).download_file(object_key, file_path)
            return {"message": "Object downloaded successfully"}
        except (ClientError, OSError) as error:
            logger.error(f"Object download failed: {error}")
            return {"message": "Object download failed"}
