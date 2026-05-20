"""
FastAPI wrapper smoke tests.

These tests validate the HTTP service layer itself: route availability,
basic response contracts, and the communication between the FastAPI wrapper
and the underlying S3 implementation. This keeps API-service smoke coverage
separate from storage-behavior smoke coverage.
"""

import logging
import pytest

from tests.fixtures.api_fixtures import api_client, api_storage, api_bucket_name


logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.smoke, pytest.mark.api]


class TestStorageApiSmoke:
    def test_get_api_service_health(self, api_client):
        """
        Validate the FastAPI health-check endpoint.

        Args:
            api_client: FastAPI test client.
        """
        # Send a GET request to check the service health
        logger.debug("Calling GET /health")
        response = api_client.get("/health")
        logger.debug("Health endpoint response: status=%s body=%s", response.status_code, response.json())

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
        # Send a POST request to bootstrap a bucket
        logger.debug("Calling POST /buckets/bootstrap with bucket_name=%s", api_bucket_name)
        response = api_client.post(
            "/buckets/bootstrap",
            params={"bucket_name": api_bucket_name},
        )
        body = response.json()
        buckets_response = api_storage.list_buckets()
        logger.debug("Bucket bootstrap response: status=%s body=%s", response.status_code, body)
        logger.debug("Bucket list response after bootstrap: %s", buckets_response)

        assert response.status_code == 200, "Bucket bootstrap did not return HTTP 200"
        assert body["status"] == "ready", "Bucket bootstrap did not report ready status"
        assert "bucket" in body, "Bucket bootstrap response is missing the bucket field"
        assert "Buckets" in buckets_response, "Bucket list response missing 'Buckets' after bootstrap"
        assert any(
            bucket["Name"] == api_bucket_name for bucket in buckets_response["Buckets"]
        ), f"Bootstrapped bucket '{api_bucket_name}' was not created"


    def test_bucket_bootstrap_idempotence(self, api_client, api_storage, api_bucket_name):
        """
        Validate that repeated bucket bootstrap calls are idempotent.

        Args:
            api_client: FastAPI test client.
            api_storage: Storage client injected into the API module.
            api_bucket_name: Unique bucket name for the current test.
        """
        # Send a POST request to bootstrap a bucket
        logger.debug("Calling first POST /buckets/bootstrap with bucket_name=%s", api_bucket_name)
        first_response = api_client.post(
            "/buckets/bootstrap",
            params={"bucket_name": api_bucket_name},
        )

        # Send a scond POST request to bootstrap a bucket
        logger.debug("Calling second POST /buckets/bootstrap with bucket_name=%s", api_bucket_name)
        second_response = api_client.post(
            "/buckets/bootstrap",
            params={"bucket_name": api_bucket_name},
        )

        # Store response bodies
        first_body = first_response.json()
        second_body = second_response.json()

        # List buckets
        buckets_response = api_storage.list_buckets()
        logger.debug(
            "Bootstrap idempotence responses: first_status=%s first_body=%s second_status=%s second_body=%s",
            first_response.status_code,
            first_body,
            second_response.status_code,
            second_body,
        )
        logger.debug("Bucket list response after repeated bootstrap: %s", buckets_response)

        assert first_response.status_code == 200, "First bootstrap call did not return HTTP 200"
        assert second_response.status_code == 200, "Second bootstrap call did not return HTTP 200"
        assert first_body["status"] == "ready", "First bootstrap call did not report ready status"
        assert second_body["status"] == "ready", "Second bootstrap call did not report ready status"
        assert "Buckets" in buckets_response, "Bucket list response missing 'Buckets' after bootstrap"

        matching_buckets = [
            bucket for bucket in buckets_response["Buckets"]
            if bucket["Name"] == api_bucket_name
        ]
        assert len(matching_buckets) == 1, (
            f"Bucket '{api_bucket_name}' should exist exactly once after repeated bootstrap calls"
        )
