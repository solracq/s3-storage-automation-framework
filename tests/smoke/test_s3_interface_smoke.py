"""
Storage implementation smoke tests.

These tests validate the shared S3 behavior contract directly against the
storage implementations (`S3Client` and `S3Resource`) without going through the
FastAPI HTTP wrapper. This keeps storage-behavior smoke coverage separate from
API-service smoke coverage.
"""

import pytest

from tests.utils.constants import OBJECT_KEY, CONTENT_DATA, FILE_PATH

from tests.fixtures.s3_fixtures import (
    storage,
    bucket_name,
    existing_bucket,
    bucket_with_object,
)


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
        response = storage.create_bucket(bucket_name)

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
        response = storage.delete_bucket(existing_bucket)

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
        response = storage.delete_object(bucket_with_object, OBJECT_KEY)
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"

        # Delete bucket with deleted objects
        response = storage.delete_bucket(bucket_with_object)
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
        response = storage.list_buckets()

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
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))
        stored_content = storage.read_object(existing_bucket, OBJECT_KEY)

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
        response = storage.list_objects(bucket_with_object)

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
        response = storage.download_object(bucket_with_object, OBJECT_KEY, str(download_path))

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
        response = storage.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        stored_content = storage.read_object(bucket_with_object, OBJECT_KEY)

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
        storage.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        response = storage.read_object(bucket_with_object, OBJECT_KEY)
        
        assert response == CONTENT_DATA, "Unsuccessful object write in response"

        
    def test_delete_object(self, storage, bucket_with_object):
        """
        Validate delete object
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Delete existing object in a bucket
        response = storage.delete_object(bucket_with_object, OBJECT_KEY)

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
        response = storage.get_object_metadata(bucket_with_object, OBJECT_KEY)
    
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
        response = storage.get_object_size(bucket_with_object, OBJECT_KEY)
        
        assert response > 0, "Object size must be bigger than zero"
