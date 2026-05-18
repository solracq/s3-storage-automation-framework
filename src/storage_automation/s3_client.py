"""
Low-level S3 access implementation built on top of ``boto3.client("s3")``.

This module keeps the storage operations close to the raw S3 API surface:
requests are expressed with explicit operation names and most successful
responses are returned as dictionaries. That makes this implementation useful
for tests that need predictable request/response handling and behavior that is
easy to compare with the underlying S3-compatible service.
"""

from io import BytesIO

import boto3
from src.storage_automation.interfaces.s3 import S3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.storage_api.settings import settings
import logging

logger = logging.getLogger(__name__)

class S3Client(S3):
    """
    Low-level S3 wrapper that uses client-style calls.

    The boto3 client API maps directly to named S3 operations such as
    ``create_bucket`` or ``head_object`` and commonly returns dictionary
    payloads. This makes the class a good fit when tests need explicit control
    over low-level calls and response inspection.
    """

    def __init__(self) -> None:
        """
        Initialize the S3 client with MinIO/S3-compatible configuration.
        """
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
        """
        Return the storage access implementation name.

        Args:
            None
        Returns:
            str: Human-readable access type label.
        """
        return "S3 Client"

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
            logger.info("Creating bucket.")
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
        """
        Delete a bucket from the configured S3-compatible storage.

        Args:
            bucket_name (str): Name of the bucket to delete.
        Returns:
            dict: Success or failure details for the delete operation.
        Raises:
            None
        """
        try:
            logger.info("Deleting bucket.")
            self.s3_client.delete_bucket(Bucket=bucket_name)
            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket deletion failed: {bucket_name}")
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
            versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            versioning_status = versioning.get("Status")

            logger.info("Emptying bucket before deletion.")
            if versioning_status in {"Enabled", "Suspended"}:
                paginator = self.s3_client.get_paginator("list_object_versions")
                for page in paginator.paginate(Bucket=bucket_name):
                    objects_to_delete = [
                        {"Key": item["Key"], "VersionId": item["VersionId"]}
                        for item in page.get("Versions", [])
                    ]
                    objects_to_delete.extend(
                        {"Key": item["Key"], "VersionId": item["VersionId"]}
                        for item in page.get("DeleteMarkers", [])
                    )

                    if objects_to_delete:
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={"Objects": objects_to_delete},
                        )
            else:
                paginator = self.s3_client.get_paginator("list_objects_v2")
                for page in paginator.paginate(Bucket=bucket_name):
                    objects_to_delete = [
                        {"Key": item["Key"]}
                        for item in page.get("Contents", [])
                    ]

                    if objects_to_delete:
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={"Objects": objects_to_delete},
                        )

            logger.info("Bucket is empty, let's delete it.")
            self.s3_client.delete_bucket(Bucket=bucket_name)
            return {"message": "Bucket deleted successfully"}
        except ClientError as error:
            logger.error(f"Bucket recursive deletion failed: {error}")
            return {"message": "Bucket deletion failed"}

    def list_buckets(self) -> dict:
        """
        List all buckets available to the configured client.

        Args:
            None
        Returns:
            dict: Raw bucket listing response or a failure message.
        Raises:
            None
        """
        try:
            logger.info("Listing buckets.")
            return self.s3_client.list_buckets()
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
            return self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
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
            return self.s3_client.head_object(Bucket=bucket_name, Key=object_key)["ContentLength"]
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
            self.s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=content)
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
            return self.s3_client.get_object(Bucket=bucket_name, Key=object_key)["Body"].read()
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
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
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
            self.s3_client.upload_file(file_path, bucket_name, object_key)
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
            self.s3_client.download_file(bucket_name, object_key, file_path)
            return {"message": "Object downloaded successfully"}
        except (ClientError, OSError) as error:
            logger.error(f"Object download failed: {error}")
            return {"message": "Object download failed"}

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> dict:
        """
        Upload in-memory bytes to the default configured bucket.

        Args:
            object_key (str): Key to assign to the uploaded object.
            content (bytes): In-memory content to upload.
            content_type (str): MIME type to store with the object.
        Returns:
            dict: Success or failure details for the upload operation.
        Raises:
            None
        """
        try:
            self.ensure_bucket_exists(self.bucket_name)
            logger.info(f"Uploading object '{object_key}' to {self.bucket_name}.")
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
        Download an object from the default bucket into memory.

        Args:
            object_key (str): Key of the object to download.
        Returns:
            tuple[BytesIO, str]: Object content as `BytesIO` plus the content type.
        Raises:
            ClientError: If the object cannot be retrieved from storage.
        """
        try:
            logger.info(f"Downloading object '{object_key}' from {self.bucket_name}.")
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
