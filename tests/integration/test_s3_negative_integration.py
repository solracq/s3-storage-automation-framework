import pytest

from tests.utils.constants import BASE_URL, BUCKET, OBJECT_KEY, CONTENT_DATA, FILE_PATH, IMAGE_PATH

from tests.fixtures.s3_fixtures import (
    storage,
    bucket_name,
    existing_bucket,
    bucket_with_object,
)


pytestmark = [pytest.mark.integration, pytest.mark.negative]


class TestS3NegativeIntegration:
    def test_create_bucket_with_existing_bucket_name(self, storage, existing_bucket):
        """
        Validate that creating a bucket with an existing name fails.

        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Create a bucket using the name of an existing bucket
        response = storage.create_bucket(existing_bucket)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response["message"] == "Bucket creation failed", "Creating a bucket with an existing name should fail"
        
        assert response["bucket_name"] == existing_bucket, "Failure response should include the duplicate bucket name"
        assert "error" in response, "Failure response should include error details"