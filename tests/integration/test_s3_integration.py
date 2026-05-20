import hashlib
import logging

import pytest

from tests.utils.constants import (
    EMPTY_FILE,
    FILE_PATH,
    IMAGE_PATH,
    LARGE_FILE,
    NEW_CONTENT,
    NON_ASCII_FILE,
    OBJECT_KEY,
)

from tests.fixtures.s3_fixtures import (
    bucket_name,
    bucket_with_object,
    existing_bucket,
    storage,
)

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.integration


class TestS3Integration:
    def test_upload_download_image_compare_checksums(self, storage, existing_bucket, tmp_path):
        """
        Validate upload/download integrity for an image using SHA-256 checksums.

        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: fixture to create a bucket for the test
            tmp_path: pytest temporary directory for downloaded files
        """
        image_object_key = IMAGE_PATH.name
        expected_content = IMAGE_PATH.read_bytes()

        # Upload an image to a bucket
        logger.debug(
            "Uploading image '%s' (%s bytes) to bucket '%s'",
            image_object_key,
            len(expected_content),
            existing_bucket,
        )
        upload_response = storage.upload_object(existing_bucket, image_object_key, str(IMAGE_PATH))
        logger.debug("Upload response: %s", upload_response)
        stored_content = storage.read_object(existing_bucket, image_object_key)
        logger.debug("Stored image content length: %s bytes", len(stored_content))

        download_path = tmp_path / image_object_key
        # Download image
        logger.debug(
            "Downloading image '%s' from bucket '%s' to '%s'",
            image_object_key,
            existing_bucket,
            download_path,
        )
        download_response = storage.download_object(existing_bucket, image_object_key, str(download_path))
        logger.debug("Download response: %s", download_response)

        # Compare original and downloaded checksums
        original_checksum = hashlib.sha256(expected_content).hexdigest()
        downloaded_checksum = hashlib.sha256(download_path.read_bytes()).hexdigest()
        logger.debug(
            "Comparing original and downloaded checksums for '%s': original=%s downloaded=%s",
            image_object_key,
            original_checksum,
            downloaded_checksum,
        )
        assert isinstance(upload_response, dict), "Upload response must be of dictionary type"
        assert upload_response["message"] == "Object uploaded successfully", "Unsuccessful image upload in response"
        assert stored_content == expected_content, "Stored image content does not match source image"
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
        logger.debug(
            "Uploading empty file '%s' as object '%s' to bucket '%s'",
            EMPTY_FILE.name,
            OBJECT_KEY,
            existing_bucket,
        )
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(EMPTY_FILE))
        logger.debug("Upload response: %s", response)
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        logger.debug("Stored empty object length: %s bytes", len(stored_content))

        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == EMPTY_FILE.read_bytes(), "Uploaded object content was not persisted correctly"

        # Delete bucket recursively, delete first objects then delete bucket
        logger.debug("Recursively deleting bucket '%s'", existing_bucket)
        response = storage.delete_bucket_recursive(existing_bucket)
        logger.debug("Bucket deletion response: %s", response)
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
        logger.debug(
            "Uploading large file '%s' (%s bytes) to bucket '%s'",
            LARGE_FILE.name,
            LARGE_FILE.stat().st_size,
            existing_bucket,
        )
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(LARGE_FILE))
        logger.debug("Upload response: %s", response)

        # Read contents of bucket
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        logger.debug("Stored large object length: %s bytes", len(stored_content))

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
        logger.debug(
            "Uploading non-ASCII file '%s' (%s bytes) to bucket '%s'",
            NON_ASCII_FILE.name,
            NON_ASCII_FILE.stat().st_size,
            existing_bucket,
        )
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(NON_ASCII_FILE))
        logger.debug("Upload response: %s", response)

        # Reading content in bucket
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        expected_content = NON_ASCII_FILE.read_bytes()
        expected_text = NON_ASCII_FILE.read_text(encoding="utf-8")
        logger.debug(
            "Comparing non-ASCII object '%s': byte_length=%s char_length=%s",
            OBJECT_KEY,
            len(stored_content),
            len(expected_text),
        )

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == expected_content, "Uploaded object content was not persisted correctly"
        assert stored_content.decode("utf-8") == expected_text, "Unsuccessful object with non-ASCII characters in response"


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
        logger.debug(
            "Overwriting object '%s' in bucket '%s': old_length=%s new_length=%s",
            OBJECT_KEY,
            bucket_with_object,
            len(existing_stored_content),
            len(NEW_CONTENT),
        )
        response = storage.write_object(bucket_with_object, OBJECT_KEY, NEW_CONTENT)
        logger.debug("Write response: %s", response)
        new_stored_content = storage.read_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Updated object '%s' length: %s", OBJECT_KEY, len(new_stored_content))

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
        logger.debug(
            "Writing initial content to object '%s' in bucket '%s': length=%s",
            object_key,
            existing_bucket,
            len(initial_content),
        )
        first_write = storage.write_object(existing_bucket, object_key, initial_content)
        logger.debug("First write response: %s", first_write)
        first_size = storage.get_object_size(existing_bucket, object_key)
        logger.debug("First recorded object size for '%s': %s", object_key, first_size)

        # Write and read second content (different size) on bucket
        logger.debug(
            "Writing updated content to object '%s' in bucket '%s': length=%s",
            object_key,
            existing_bucket,
            len(updated_content),
        )
        second_write = storage.write_object(existing_bucket, object_key, updated_content)
        logger.debug("Second write response: %s", second_write)
        second_size = storage.get_object_size(existing_bucket, object_key)
        logger.debug("Second recorded object size for '%s': %s", object_key, second_size)

        assert first_write["message"] == "Object written successfully", "A problem ocurr wirting on the object"
        assert first_size == len(initial_content), "File size and inital size content in file should match"

        assert second_write["message"] == "Object written successfully", "A problem ocurr wirting on the object"
        assert second_size == len(updated_content), "File size and second size content in file should match"
        # Confirm object size changes afer overwriting the content of the object
        assert second_size != first_size, "File sizes should differ as loading content size differ"


    def test_delete_object_then_confirm_removal(self, storage, bucket_with_object):
        """
        Validate that deleting an object removes it from the bucket.

        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: bucket fixture that already contains OBJECT_KEY
        """
        # Delete existing object in bucket
        logger.debug("Deleting object '%s' in bucket: %s", OBJECT_KEY, bucket_with_object)
        delete_response = storage.delete_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Delete response: %s", delete_response)

        # List buckets after deletion
        objects_after_delete = storage.list_objects(bucket_with_object)
        logger.debug("Objects remaining in bucket '%s': %s", bucket_with_object, len(objects_after_delete))

        # Look for object by reading it
        read_response = storage.read_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Read-after-delete response: %s", read_response)

        # Confirm object has been deleted
        assert isinstance(delete_response, dict), "Delete response must be of dictionary type"
        assert delete_response["message"] == "Object deleted successfully", "Unsuccessful object deletion in response"

        # Confirm object is not present after deletion
        assert all(obj["key"] != OBJECT_KEY for obj in objects_after_delete), "Deleted object is still listed in bucket contents"

        # Confirm object content cannot be read as it has been deleted
        assert isinstance(read_response, dict), "Deleted object read should return a failure response"
        assert read_response["message"] == "Object reading failed", "Deleted object should not be readable after removal"


    def test_create_upload_list_download_compare_delete_file_lifecycle(self, storage, existing_bucket, tmp_path):
        """
        Validate create bucket, upload file, list object, download it, compare content,
        then delete it and confirm removal.

        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
            tmp_path: pytest temporary directory for downloaded files
        """
        object_key = FILE_PATH.name
        expected_content = FILE_PATH.read_bytes()

        # Upload file
        logger.debug(
            "Uploading lifecycle file '%s' (%s bytes) to bucket '%s' as object '%s'",
            FILE_PATH.name,
            len(expected_content),
            existing_bucket,
            object_key,
        )
        upload_response = storage.upload_object(existing_bucket, object_key, str(FILE_PATH))
        logger.debug("Upload response: %s", upload_response)

        # List objects and confirm the uploaded file appears
        objects_after_upload = storage.list_objects(existing_bucket)
        logger.debug("Objects listed after upload in bucket '%s': %s", existing_bucket, len(objects_after_upload))

        # Download file
        download_path = tmp_path / object_key
        logger.debug(
            "Downloading lifecycle file '%s' from bucket '%s' to '%s'",
            object_key,
            existing_bucket,
            download_path,
        )
        download_response = storage.download_object(existing_bucket, object_key, str(download_path))
        logger.debug("Download response: %s", download_response)

        # Compare original and downloaded content
        downloaded_content = download_path.read_bytes()
        logger.debug(
            "Comparing lifecycle file content lengths: expected=%s downloaded=%s",
            len(expected_content),
            len(downloaded_content),
        )

        # Delete file
        logger.debug("Deleting lifecycle file '%s' from bucket '%s'", object_key, existing_bucket)
        delete_response = storage.delete_object(existing_bucket, object_key)
        logger.debug("Delete response: %s", delete_response)

        # Confirm removal
        objects_after_delete = storage.list_objects(existing_bucket)
        read_after_delete = storage.read_object(existing_bucket, object_key)
        logger.debug("Objects listed after delete in bucket '%s': %s", existing_bucket, len(objects_after_delete))
        logger.debug("Read-after-delete response: %s", read_after_delete)

        assert isinstance(upload_response, dict), "Upload response must be of dictionary type"
        assert upload_response["message"] == "Object uploaded successfully", "Unsuccessful file upload in response"

        assert any(obj["key"] == object_key for obj in objects_after_upload), "Uploaded file is not listed in the bucket"

        assert isinstance(download_response, dict), "Download response must be of dictionary type"
        assert download_response["message"] == "Object downloaded successfully", "Unsuccessful file download in response"
        assert download_path.exists(), "Downloaded file was not created"
        assert downloaded_content == expected_content, "Downloaded file content does not match the uploaded file"

        assert isinstance(delete_response, dict), "Delete response must be of dictionary type"
        assert delete_response["message"] == "Object deleted successfully", "Unsuccessful file deletion in response"

        assert all(obj["key"] != object_key for obj in objects_after_delete), "Deleted file is still listed in the bucket"
        assert isinstance(read_after_delete, dict), "Reading a deleted file should return a failure response"
        assert read_after_delete["message"] == "Object reading failed", "Deleted file should not be readable after removal"


    def test_upload_empty_file_to_bucket_is_allowed(self, storage, existing_bucket):
        """
        Validate response correctness when uploading an empty file to a bucket.
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload an empty file to an existing bucket
        logger.debug(
            "Uploading empty file '%s' to bucket '%s' as object '%s'",
            EMPTY_FILE.name,
            existing_bucket,
            OBJECT_KEY,
        )
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(EMPTY_FILE))
        logger.debug("Upload response: %s", response)

        # Read empty content
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        logger.debug("Stored empty file length: %s bytes", len(stored_content))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == EMPTY_FILE.read_bytes(), "Uploaded object content was not persisted correctly"
