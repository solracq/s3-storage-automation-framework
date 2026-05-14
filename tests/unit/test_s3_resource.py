from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.storage_automation import s3_resource as s3_resource_module

pytestmark = pytest.mark.unit


@pytest.fixture
def resource_instance(monkeypatch):
    """
    Build an S3Resource instance with boto3 replaced by a mock resource object.
    """
    sdk_resource = MagicMock()

    monkeypatch.setattr(s3_resource_module.boto3, "resource", MagicMock(return_value=sdk_resource))
    monkeypatch.setattr(s3_resource_module.settings, "minio_bucket_name", "test-bucket")
    monkeypatch.setattr(s3_resource_module.settings, "s3_endpoint_url", "http://localhost:9000")
    monkeypatch.setattr(s3_resource_module.settings, "aws_access_key_id", "minioadmin")
    monkeypatch.setattr(s3_resource_module.settings, "aws_secret_access_key", "minioadmin")
    monkeypatch.setattr(s3_resource_module.settings, "aws_region", "us-east-1")

    return s3_resource_module.S3Resource(), sdk_resource


def test_delete_bucket_uses_object_versions_when_versioning_is_enabled(resource_instance):
    """
    Example of testing a branch that only exists in the resource implementation.
    """
    s3_resource, sdk_resource = resource_instance
    bucket = MagicMock()
    sdk_resource.Bucket.return_value = bucket
    sdk_resource.BucketVersioning.return_value.status = "Enabled"

    result = s3_resource.delete_bucket("versioned-bucket")

    assert result == {"message": "Bucket deleted successfully"}
    bucket.object_versions.delete.assert_called_once_with()
    bucket.objects.all.assert_not_called()
    bucket.delete.assert_called_once_with()


def test_delete_bucket_uses_object_listing_when_versioning_is_not_enabled(resource_instance):
    """
    Example of checking the alternate cleanup branch before bucket deletion.
    """
    s3_resource, sdk_resource = resource_instance
    bucket = MagicMock()
    objects_collection = MagicMock()
    bucket.objects.all.return_value = objects_collection
    sdk_resource.Bucket.return_value = bucket
    sdk_resource.BucketVersioning.return_value.status = None

    result = s3_resource.delete_bucket("plain-bucket")

    assert result == {"message": "Bucket deleted successfully"}
    bucket.objects.all.assert_called_once_with()
    objects_collection.delete.assert_called_once_with()
    bucket.object_versions.delete.assert_not_called()
    bucket.delete.assert_called_once_with()


def test_list_objects_maps_resource_items_to_simple_dicts(resource_instance):
    """
    Example of validating that higher-level resource objects are normalized into
    the same lightweight structure the rest of the app expects.
    """
    s3_resource, sdk_resource = resource_instance
    object_summary = MagicMock()
    object_summary.key = "sample.txt"
    object_summary.size = 12
    object_summary.last_modified = datetime(2026, 5, 14, 12, 30, tzinfo=timezone.utc)

    sdk_resource.Bucket.return_value.objects.all.return_value = [object_summary]

    result = s3_resource.list_objects("test-bucket")

    assert result == [
        {
            "key": "sample.txt",
            "size": 12,
            "last_modified": "2026-05-14T12:30:00+00:00",
        }
    ]


def test_write_object_puts_content_through_resource_object(resource_instance):
    """
    Example of asserting the object-oriented resource call shape.
    """
    s3_resource, sdk_resource = resource_instance
    s3_resource.ensure_bucket_exists = MagicMock()
    object_handle = MagicMock()
    sdk_resource.Object.return_value = object_handle

    result = s3_resource.write_object("test-bucket", "sample.txt", b"hello")

    assert result == {"message": "Object written successfully"}
    s3_resource.ensure_bucket_exists.assert_called_once_with("test-bucket")
    sdk_resource.Object.assert_called_once_with("test-bucket", "sample.txt")
    object_handle.put.assert_called_once_with(Body=b"hello")
