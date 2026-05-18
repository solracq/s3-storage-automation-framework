import hashlib

import pytest

from tests.utils.constants import OBJECT_KEY, IMAGE_PATH

from tests.fixtures.s3_fixtures import (
    storage,
    bucket_name,
    existing_bucket,
    bucket_with_object,
)


pytestmark = pytest.mark.integration


class TestS3Integration:
    def test_upload_download_image_compare_checksums(self, storage, bucket_name, existing_bucket, tmp_path):
        """
        Validate upload/download integrity for an image using SHA-256 checksums.

        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: fixture to create a bucket for the test
            tmp_path: pytest temporary directory for downloaded files
        """
        image_object_key = IMAGE_PATH.name

        upload_response = storage.upload_object(existing_bucket, image_object_key, str(IMAGE_PATH))
        stored_content = storage.read_object(existing_bucket, image_object_key)

        download_path = tmp_path / image_object_key
        download_response = storage.download_object(existing_bucket, image_object_key, str(download_path))

        original_checksum = hashlib.sha256(IMAGE_PATH.read_bytes()).hexdigest()
        downloaded_checksum = hashlib.sha256(download_path.read_bytes()).hexdigest()

        assert isinstance(upload_response, dict), "Upload response must be of dictionary type"
        assert upload_response["message"] == "Object uploaded successfully", "Unsuccessful image upload in response"
        assert stored_content == IMAGE_PATH.read_bytes(), "Stored image content does not match source image"
        assert isinstance(download_response, dict), "Download response must be of dictionary type"
        assert download_response["message"] == "Object downloaded successfully", "Unsuccessful image download in response"
        assert download_path.exists(), "Downloaded image file was not created"
        assert original_checksum == downloaded_checksum, "Downloaded image checksum does not match original image checksum"
