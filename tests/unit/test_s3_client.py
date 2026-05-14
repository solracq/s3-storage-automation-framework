from unittest.mock import MagicMock

import pytest

from conftest import make_client_error
from src.storage_automation import s3_client as s3_client_module

pytestmark = pytest.mark.unit


@pytest.fixture
def client_instance(monkeypatch):
    """
    Build an S3Client instance with boto3 replaced by a plain mock.

    This keeps the test fully local: no MinIO container, no AWS calls, and no
    dependency on real credentials.
    """
    # Create a fake S3 SDK client
    sdk_client = MagicMock()

    monkeypatch.setattr(s3_client_module.boto3, "client", MagicMock(return_value=sdk_client)) # Patching boto3.client so the constructor recieives the fake sdk_cient instead
    monkeypatch.setattr(s3_client_module.settings, "minio_bucket_name", "test-bucket") # Patching settings values
    monkeypatch.setattr(s3_client_module.settings, "s3_endpoint_url", "http://localhost:9000")
    monkeypatch.setattr(s3_client_module.settings, "aws_access_key_id", "minioadmin")
    monkeypatch.setattr(s3_client_module.settings, "aws_secret_access_key", "minioadmin")
    monkeypatch.setattr(s3_client_module.settings, "aws_region", "us-east-1")

    return s3_client_module.S3Client(), sdk_client


def test_ensure_bucket_exists_creates_missing_bucket(client_instance):
    """
    Example of testing control flow:
    when head_bucket says "not found", the class should create the bucket.
    """
    s3_client, sdk_client = client_instance
    sdk_client.head_bucket.side_effect = make_client_error("404", "HeadBucket")
    s3_client.create_bucket = MagicMock(return_value={"message": "Bucket created successfully"})

    s3_client.ensure_bucket_exists("new-bucket")

    s3_client.create_bucket.assert_called_once_with("new-bucket")


def test_create_bucket_adds_location_constraint_outside_us_east_1(client_instance, monkeypatch):
    """
    Example of asserting the exact low-level boto3 call payload.
    """
    s3_client, sdk_client = client_instance
    monkeypatch.setattr(s3_client_module.settings, "aws_region", "ca-central-1")

    result = s3_client.create_bucket("region-bucket")

    assert result == {"message": "Bucket created successfully"}
    sdk_client.create_bucket.assert_called_once_with(
        Bucket="region-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ca-central-1"},
    )


def test_upload_bytes_uses_default_bucket_and_content_type(client_instance):
    """
    Example of checking both the response and the SDK call made by the unit.
    """
    s3_client, sdk_client = client_instance
    s3_client.ensure_bucket_exists = MagicMock()

    result = s3_client.upload_bytes("sample.txt", b"hello", "text/plain")

    assert result == {
        "bucket": "test-bucket",
        "object_key": "sample.txt",
        "content_type": "text/plain",
        "message": "Object uploaded successfully",
    }
    s3_client.ensure_bucket_exists.assert_called_once_with("test-bucket")
    sdk_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="sample.txt",
        Body=b"hello",
        ContentType="text/plain",
    )


def test_download_file_returns_bytes_and_content_type(client_instance):
    """
    Example of validating a transformation: boto3 response -> BytesIO tuple.
    """
    s3_client, sdk_client = client_instance
    body = MagicMock()
    body.read.return_value = b"hello world"
    sdk_client.get_object.return_value = {
        "Body": body,
        "ContentType": "text/plain",
    }

    file_stream, content_type = s3_client.download_file("sample.txt")

    assert file_stream.getvalue() == b"hello world"
    assert content_type == "text/plain"
    sdk_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="sample.txt")
