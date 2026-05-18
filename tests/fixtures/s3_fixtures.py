import warnings

import pytest
from uuid import uuid4

from src.storage_automation import s3_client as s3_client_module
from src.storage_automation import s3_resource as s3_resource_module
from src.storage_automation.s3_client import S3Client
from src.storage_automation.s3_resource import S3Resource
from tests.utils.constants import BASE_URL, BUCKET, OBJECT_KEY, FILE_PATH


@pytest.fixture(
    params=[
        ("client", s3_client_module, S3Client),
        ("resource", s3_resource_module, S3Resource),
    ],
    ids=["client", "resource"],
)
def storage(request, monkeypatch):
    _, module, s3_cls = request.param
    monkeypatch.setattr(module.settings, "s3_endpoint_url", BASE_URL)
    return s3_cls()


@pytest.fixture
def bucket_name(storage):
    """
    Provide a unique bucket name per test and always attempt cleanup.
    """
    name = f"{BUCKET}-{uuid4().hex[:8]}"
    yield name

    buckets_response = storage.list_buckets()
    if "Buckets" not in buckets_response:
        warnings.warn(
            f"Teardown could not verify bucket cleanup for '{name}': {buckets_response}",
            stacklevel=2,
        )
        return

    bucket_exists = any(bucket["Name"] == name for bucket in buckets_response["Buckets"])
    if not bucket_exists:
        return

    for obj in storage.list_objects(name):
        delete_object_response = storage.delete_object(name, obj["key"])
        if delete_object_response.get("message") != "Object deleted successfully":
            warnings.warn(
                f"Teardown failed to delete object '{obj['key']}' from bucket '{name}': "
                f"{delete_object_response}",
                stacklevel=2,
            )

    delete_bucket_response = storage.delete_bucket(name)
    if delete_bucket_response.get("message") != "Bucket deleted successfully":
        warnings.warn(
            f"Teardown failed to delete bucket '{name}': {delete_bucket_response}",
            stacklevel=2,
        )


@pytest.fixture
def existing_bucket(storage, bucket_name):
    """
    Create a bucket for tests that need an existing bucket.
    """
    response = storage.create_bucket(bucket_name)
    assert response["message"] == "Bucket created successfully"
    return bucket_name


@pytest.fixture
def bucket_with_object(storage, existing_bucket):
    """
    Create a bucket and upload a fixture object for object-level smoke tests.
    """
    response = storage.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))
    assert response["message"] == "Object uploaded successfully"
    return existing_bucket
