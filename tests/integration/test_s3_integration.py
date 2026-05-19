import hashlib

import pytest

from tests.utils.constants import OBJECT_KEY, IMAGE_PATH, EMPTY_FILE, LARGE_FILE, NON_ASCII_FILE

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

        # Upload an image to a bucket
        upload_response = storage.upload_object(existing_bucket, image_object_key, str(IMAGE_PATH))
        # Read content in bucket
        stored_content = storage.read_object(existing_bucket, image_object_key)

        download_path = tmp_path / image_object_key
        # Download image
        download_response = storage.download_object(existing_bucket, image_object_key, str(download_path))

        # Compare original and downlaoded checksums
        original_checksum = hashlib.sha256(IMAGE_PATH.read_bytes()).hexdigest()
        downloaded_checksum = hashlib.sha256(download_path.read_bytes()).hexdigest()

        assert isinstance(upload_response, dict), "Upload response must be of dictionary type"
        assert upload_response["message"] == "Object uploaded successfully", "Unsuccessful image upload in response"
        assert stored_content == IMAGE_PATH.read_bytes(), "Stored image content does not match source image"
        assert isinstance(download_response, dict), "Download response must be of dictionary type"
        assert download_response["message"] == "Object downloaded successfully", "Unsuccessful image download in response"
        assert download_path.exists(), "Downloaded image file was not created"
        assert original_checksum == downloaded_checksum, "Downloaded image checksum does not match original image checksum"


    def test_delete_bucket_recursively_with_empty_file(self, storage, existing_bucket):
        """
        Validate recursive deletion of a bucket that contains an empty object
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload an empty object to a bucket
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(EMPTY_FILE))
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)

        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == EMPTY_FILE.read_bytes(), "Uploaded object content was not persisted correctly"

        # Delete bucket recursively, delete first objects then delete bucket
        response = storage.delete_bucket_recursive(existing_bucket)
        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"


    def test_upload_large_file_within_limit(self, storage, existing_bucket):
        """
        Validate uploading of object with max_part_size (allowed) = 1024 * 1024 (1 MB)
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload a large object to a bucket
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(LARGE_FILE))

        # Read contents of bucket
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == LARGE_FILE.read_bytes(), "Uploaded object content was not persisted correctly"


    def test_upload_file_with_non_ascii_chars(self, storage, existing_bucket):
        """
        Validate uploading and reading an object containing non-ASCII characters.
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload a file containing non-ASCII characters
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(NON_ASCII_FILE))

        # Reading content in bucket
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        expected_content = NON_ASCII_FILE.read_bytes()
        expected_text = NON_ASCII_FILE.read_text(encoding="utf-8")

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == expected_content, "Uploaded object content was not persisted correctly"
        assert stored_content.decode("utf-8") == expected_text, (
            "Unsuccessful object with non-ASCII characters in response"
        )


    def test_overwrite_existing_content_reads_new_content(self, storage, bucket_with_object):
        """
        Validate when overwriting an existing content in an object, reading content will show 
        the new content.
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Read data in object
        existing_stored_content = storage.read_object(bucket_with_object, OBJECT_KEY)

        # Overwrite an existing content in an object
        new_content = "New data added"
        response = storage.write_object(bucket_with_object, OBJECT_KEY, new_content)
        new_stored_content = storage.read_object(bucket_with_object, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object written successfully", "Unsuccessful object write in response"
        assert new_stored_content != existing_stored_content, "Object content was not overwritten correctly"


    def test_get_object_size_changes_as_data_gets_updated(self, storage, existing_bucket):
        """
        Validate that object size changes after overwriting the object content.

        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        object_key = "size-check.txt"
        initial_content = b"abc"
        updated_content = b"abcdefghij"

        # Write and read initial content on bucket
        first_write = storage.write_object(existing_bucket, object_key, initial_content)
        first_size = storage.get_object_size(existing_bucket, object_key)

        # Write and read second content (different size) on bucket
        second_write = storage.write_object(existing_bucket, object_key, updated_content)
        second_size = storage.get_object_size(existing_bucket, object_key)

        assert first_write["message"] == "Object written successfully"
        assert first_size == len(initial_content)

        assert second_write["message"] == "Object written successfully"
        assert second_size == len(updated_content)
        # Confirm object size changes afer overwriting the content of the object
        assert second_size != first_size


    def test_delete_object_then_confirm_removal(self, storage, bucket_with_object):
        """
        Validate that deleting an object removes it from the bucket.

        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: bucket fixture that already contains OBJECT_KEY
        """
        # Delete existing object in bucket
        delete_response = storage.delete_object(bucket_with_object, OBJECT_KEY)

        # List buckets after deletion
        objects_after_delete = storage.list_objects(bucket_with_object)

        # Look for object by reading it
        read_response = storage.read_object(bucket_with_object, OBJECT_KEY)

        # Confirm object has been deleted
        assert isinstance(delete_response, dict), "Delete response must be of dictionary type"
        assert delete_response["message"] == "Object deleted successfully", (
            "Unsuccessful object deletion in response"
        )

        # Confirm object is not present after deletion
        assert all(obj["key"] != OBJECT_KEY for obj in objects_after_delete), (
            "Deleted object is still listed in bucket contents"
        )

        # Confirm object content cannot be read as it has been deleted
        assert isinstance(read_response, dict), "Deleted object read should return a failure response"
        assert read_response["message"] == "Object reading failed", (
            "Deleted object should not be readable after removal"
        )
