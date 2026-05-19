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

