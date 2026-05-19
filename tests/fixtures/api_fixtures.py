from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.storage_api import main as main_module
from src.storage_automation import s3_client as s3_client_module
from src.storage_automation.s3_client import S3Client
from tests.utils.constants import BASE_URL, BUCKET
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
def api_storage(monkeypatch):
    """
    Patch the S3 endpoint and inject a fresh `S3Client` into `main.py`.

    Args:
        monkeypatch: Pytest fixture used to patch module attributes.
    Returns:
        S3Client: Fresh storage client instance used by the API layer.
    """
    monkeypatch.setattr(s3_client_module.settings, "s3_endpoint_url", BASE_URL)
    storage = S3Client()
    logger.debug("Using '%s' implementation", storage)
    monkeypatch.setattr(main_module, "storage", storage)
    return storage


@pytest.fixture
def api_client(api_storage):
    """
    Create a FastAPI test client for the storage API.

    Args:
        api_storage: Injected storage client for the API module.
    Returns:
        TestClient: Client used to send HTTP requests to the FastAPI app.
    """
    return TestClient(main_module.app)


@pytest.fixture
def api_bucket_name(api_storage):
    """
    Generate a unique bucket name for API tests and clean it up after use.

    Args:
        api_storage: Storage client used for post-test cleanup.
    Yields:
        str: Unique bucket name for the current test.
    """
    name = f"{BUCKET}-api-{uuid4().hex[:8]}"
    logger.debug("Generated bucket name, '%s'", name)
    yield name

    buckets_response = api_storage.list_buckets()
    logger.debug("List buckets response, '%s'", buckets_response)
    if "Buckets" not in buckets_response:
        return

    logger.debug("Checking if bucket exists in response, '%s'", buckets_response["Buckets"])
    bucket_exists = any(bucket["Name"] == name for bucket in buckets_response["Buckets"])
    if not bucket_exists:
        return

    for obj in api_storage.list_objects(name):
        logger.debug("Deleting object '%s' with key '%s'", name, obj["key"])
        api_storage.delete_object(name, obj["key"])

    logger.debug("Deleting bucket : %s", name)
    api_storage.delete_bucket(name)
