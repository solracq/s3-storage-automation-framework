"""
Storage implementation smoke tests.

These tests validate the shared S3 behavior contract directly against the
storage implementations (`S3Client` and `S3Resource`) without going through the
FastAPI HTTP wrapper. This keeps storage-behavior smoke coverage separate from
API-service smoke coverage.
"""

import logging
import pytest

from tests.utils.constants import (
    CONTENT_DATA,
    FILE_PATH,
    OBJECT_KEY,
)


from tests.fixtures.s3_fixtures import (
    bucket_name,
    bucket_with_object,
    existing_bucket,
    storage,
)


logger = logging.getLogger(__name__)

pytestmark = pytest.mark.smoke


class TestS3InterfaceSmoke:
    def test_create_bucket(self, storage, bucket_name):
        """
        Validate creation of a bucket
        Args:
            storage: s3 storage (client or resource) object
            bucket_name: unique bucket name for the test
        """
        # Create bucket
        logger.debug("Creating smoke-test bucket '%s'", bucket_name)
        response = storage.create_bucket(bucket_name)
        logger.debug("Create bucket response: %s", response)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket created successfully", "Unsuccessful bucket creation in response"


    def test_delete_empty_bucket(self, storage, existing_bucket):
        """
        Validate deletion of an empty bucket
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Delete emtpy bucket (no objects in bucket)
        logger.debug("Deleting empty smoke-test bucket '%s'", existing_bucket)
        response = storage.delete_bucket(existing_bucket)
        logger.debug("Delete empty bucket response: %s", response)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"

    
    def test_delete_bucket_with_objects(self, storage, bucket_with_object):
        """
        Validate deletion of a bucket that contains objects
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Delete first objects in bucket
        logger.debug(
            "Deleting object '%s' from smoke-test bucket '%s' before bucket deletion",
            OBJECT_KEY,
            bucket_with_object,
        )
        response = storage.delete_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Delete object response: %s", response)
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"

        # Delete bucket with deleted objects
        logger.debug("Deleting smoke-test bucket '%s' after object cleanup", bucket_with_object)
        response = storage.delete_bucket(bucket_with_object)
        logger.debug("Delete bucket response: %s", response)
        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"


    def test_list_buckets(self, storage, existing_bucket):
        """
        Validate listing bucket(s)
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # List buckets
        logger.debug("Listing buckets to confirm '%s' is present", existing_bucket)
        response = storage.list_buckets()
        logger.debug("List buckets response: %s", response)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert "Buckets" in response, "'Buckets' string missing in response"
        assert any(bucket["Name"] == existing_bucket for bucket in response["Buckets"]), f"Bucket name '{existing_bucket}' is missing in response"


    def test_upload_object(self, storage, existing_bucket):
        """
        Validate uploading of an object onto a bucket
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload an object / file to an existing bucket
        logger.debug(
            "Uploading smoke fixture '%s' (%s bytes) to bucket '%s' as object '%s'",
            FILE_PATH.name,
            FILE_PATH.stat().st_size,
            existing_bucket,
            OBJECT_KEY,
        )
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)
        logger.debug("Upload response: %s", response)
        logger.debug("Stored object length after upload: %s bytes", len(stored_content))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"
        assert stored_content == FILE_PATH.read_bytes(), "Uploaded object content was not persisted correctly"


    def test_list_objects(self, storage, bucket_with_object):
        """
        Validate listing objects in a bucket
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # list objects in an existing bucket
        logger.debug("Listing objects in smoke-test bucket '%s'", bucket_with_object)
        response = storage.list_objects(bucket_with_object)
        logger.debug("List objects response count: %s", len(response))

        assert response[0]['key'] == OBJECT_KEY, "Object key is not available in response"
        assert int(response[0]['size']) > 0, "Object size is not available in response"
        assert response[0]['last_modified'], "Object 'last_modified' info is not available in response"


    def test_download_object(self, storage, bucket_with_object, tmp_path):
        """
        Validate download of an object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
            tmp_path: pytest temporary directory for downloaded files
        """
        # Download object in bucket
        download_path = tmp_path / OBJECT_KEY
        logger.debug(
            "Downloading object '%s' from bucket '%s' to '%s'",
            OBJECT_KEY,
            bucket_with_object,
            download_path,
        )
        response = storage.download_object(bucket_with_object, OBJECT_KEY, str(download_path))
        logger.debug("Download response: %s", response)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object downloaded successfully", "Unsuccessful object download in response"
        assert download_path.exists(), "Downloaded file was not created"
        assert download_path.read_bytes() == FILE_PATH.read_bytes(), "Downloaded object content does not match source fixture data"


    def test_write_object(self, storage, bucket_with_object):
        """
        Validate write data to an object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Write to an existing object in a bucket
        logger.debug(
            "Writing smoke content to object '%s' in bucket '%s': length=%s",
            OBJECT_KEY,
            bucket_with_object,
            len(CONTENT_DATA),
        )
        response = storage.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        stored_content = storage.read_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Write response: %s", response)
        logger.debug("Stored object length after write: %s bytes", len(stored_content))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object written successfully", "Unsuccessful object write in response"
        assert stored_content == CONTENT_DATA, "Written object content was not persisted correctly"


    def test_read_object(self, storage, bucket_with_object):
        """
        Validate read data from an object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Read data in object
        logger.debug(
            "Preparing object '%s' in bucket '%s' for smoke read test",
            OBJECT_KEY,
            bucket_with_object,
        )
        write_response = storage.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        logger.debug("Preparation write response: %s", write_response)
        response = storage.read_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Read object length: %s bytes", len(response))
        
        assert response == CONTENT_DATA, "Unsuccessful object write in response"

        
    def test_delete_object(self, storage, bucket_with_object):
        """
        Validate delete object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Delete existing object in a bucket
        logger.debug("Deleting object '%s' from smoke-test bucket '%s'", OBJECT_KEY, bucket_with_object)
        response = storage.delete_object(bucket_with_object, OBJECT_KEY)
        logger.debug("Delete object response: %s", response)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['bucket_name'] == bucket_with_object, "Deleted bucket name not in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"


    def test_get_object_metadata(self, storage, bucket_with_object):
        """
        Validate object metadata from an object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Obtain the object metadata in bucket
        logger.debug("Retrieving metadata for object '%s' in bucket '%s'", OBJECT_KEY, bucket_with_object)
        response = storage.get_object_metadata(bucket_with_object, OBJECT_KEY)
        logger.debug("Metadata response keys: %s", list(response.keys()))
    
        assert response["ContentLength"] > 0, "'ContentLength' missed in metadata"
        assert response["LastModified"], "'LastModified' missed in metadata"
        assert response["ETag"], "'ETag' missed in metadata"
        assert response["ContentType"], "'ContentType' missed in metadata"


    def test_get_object_size(self, storage, bucket_with_object):
        """
        Validate object size from an object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Obtain object size in bucket
        logger.debug("Retrieving size for object '%s' in bucket '%s'", OBJECT_KEY, bucket_with_object)
        response = storage.get_object_size(bucket_with_object, OBJECT_KEY)
        logger.debug("Object size response: %s bytes", response)
        
        assert response > 0, "Object size must be bigger than zero"
