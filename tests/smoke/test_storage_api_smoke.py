"""
FastAPI wrapper smoke tests.

These tests validate the HTTP service layer itself: route availability,
basic response contracts, and the communication between the FastAPI wrapper
and the underlying S3 implementation. This keeps API-service smoke coverage
separate from storage-behavior smoke coverage.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.storage_api import main as main_module
from src.storage_automation import s3_client as s3_client_module
from src.storage_automation.s3_client import S3Client
from tests.utils.constants import BASE_URL, BUCKET


pytestmark = [pytest.mark.smoke, pytest.mark.api]


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
    Generate a unique bucket name for API smoke tests and clean it up after use.

    Args:
        api_storage: Storage client used for post-test cleanup.
    Yields:
        str: Unique bucket name for the current test.
    """
    name = f"{BUCKET}-api-{uuid4().hex[:8]}"
    yield name

    buckets_response = api_storage.list_buckets()
    if "Buckets" not in buckets_response:
        return

    bucket_exists = any(bucket["Name"] == name for bucket in buckets_response["Buckets"])
    if not bucket_exists:
        return

    for obj in api_storage.list_objects(name):
        api_storage.delete_object(name, obj["key"])

    api_storage.delete_bucket(name)


class TestStorageApiSmoke:
    def test_get_api_service_health(self, api_client):
        """
        Validate the FastAPI health-check endpoint.

        Args:
            api_client: FastAPI test client.
        """
        response = api_client.get("/health")

        assert response.status_code == 200, "Health endpoint did not return HTTP 200"
        assert response.json() == {
            "status": "ok",
            "service": "storage-api",
        }, "Health endpoint response payload is incorrect"

    def test_bucket_bootstrap(self, api_client, api_storage, api_bucket_name):
        """
        Validate bucket bootstrap through the FastAPI wrapper.

        Args:
            api_client: FastAPI test client.
            api_storage: Storage client injected into the API module.
            api_bucket_name: Unique bucket name for the current test.
        """
        response = api_client.post(
            "/buckets/bootstrap",
            params={"bucket_name": api_bucket_name},
        )
        body = response.json()
        buckets_response = api_storage.list_buckets()

        assert response.status_code == 200, "Bucket bootstrap did not return HTTP 200"
        assert body["status"] == "ready", "Bucket bootstrap did not report ready status"
        assert "bucket" in body, "Bucket bootstrap response is missing the bucket field"
        assert "Buckets" in buckets_response, "Bucket list response missing 'Buckets' after bootstrap"
        assert any(
            bucket["Name"] == api_bucket_name for bucket in buckets_response["Buckets"]
        ), f"Bootstrapped bucket '{api_bucket_name}' was not created"
