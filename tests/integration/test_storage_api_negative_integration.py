"""
FastAPI wrapper negative integration tests.

These tests validate HTTP-layer error handling and request validation for the
FastAPI wrapper.
"""

import pytest

from tests.fixtures.api_fixtures import api_client, api_storage, api_bucket_name
from tests.utils.constants import EMPTY_FILE


pytestmark = [pytest.mark.integration, pytest.mark.negative, pytest.mark.api]


class TestStorageApiNegativeIntegration:
    def test_upload_empty_file_to_bucket(self, api_client):
        """
        Validate uploading an empty file through the API is rejected.

        Args:
            api_client: FastAPI test client.
        """
        # Send a POST request to upload an empty file
        with EMPTY_FILE.open("rb") as empty_file:
            response = api_client.post(
                f"/files/{EMPTY_FILE.name}",
                files={"file": (EMPTY_FILE.name, empty_file, "text/plain")},
            )

        assert response.status_code == 400, "Empty file upload did not return HTTP 400"
        assert response.json() == {"detail": "File content cannot be empty"}, "Empty file upload response payload is incorrect"


    def test_call_endpoint_requiring_bucket_name_without_query_param(self, api_client):
        """
        Validate FastAPI rejects requests that omit the required `bucket_name` query parameter.

        Args:
            api_client: FastAPI test client.
        """
        # Send GET request without the required bucket_name query parameter
        response = api_client.get("/files")
        body = response.json()

        assert response.status_code == 422, "Missing bucket_name did not return HTTP 422"
        assert "detail" in body, "Validation error response is missing the detail field"
        assert any(
            error["loc"] == ["query", "bucket_name"] and error["type"] == "missing"
            for error in body["detail"]
        ), "Validation error did not identify the missing bucket_name query parameter"


    def test_upload_request_without_multipart_file_field(self, api_client):
        """
        Validate FastAPI rejects upload requests that omit the required multipart `file` field.

        Args:
            api_client: FastAPI test client.
        """
        # Send a POST request without the required multipart file field
        response = api_client.post(f"/files/{EMPTY_FILE.name}")
        body = response.json()

        assert response.status_code == 422, "Missing multipart file field did not return HTTP 422"
        assert "detail" in body, "Validation error response is missing the detail field"
        assert any(
            error["loc"] == ["body", "file"] and error["type"] == "missing"
            for error in body["detail"]
        ), "Validation error did not identify the missing multipart file field"


    def test_write_object_with_empty_data(self, api_client, api_bucket_name):
        """
        Validate FastAPI rejects write-object requests with an empty request body.

        Args:
            api_client: FastAPI test client.
            api_bucket_name: Unique bucket name for the current test.
        """
        # Send a PUT request with the required bucket_name query parameter but no body content
        response = api_client.put(
            f"/objects/{EMPTY_FILE.name}",
            params={"bucket_name": api_bucket_name},
            content=b"",
        )

        assert response.status_code == 400, "Empty write-object request did not return HTTP 400"
        assert response.json() == {
            "detail": "Request body cannot be empty"
        }, "Empty write-object response payload is incorrect"

