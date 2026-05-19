import pytest

from tests.utils.constants import BASE_URL, BUCKET, OBJECT_KEY, CONTENT_DATA, FILE_PATH, EMPTY_FILE, LARGE_FILE_SIZE_LIMIT_EXEEDED

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

    def test_get_list_of_buckets_when_no_buckets(self, storage):
        """
        Validate correct response when getting an emtpy list of buckets.

        Args:
            storage: s3 storage (client or resource) object
        """
        # List buckets
        response = storage.list_buckets()

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert "Buckets" in response, "'Buckets' string missing in response"
        assert response["Buckets"] == [], f"List of buckets is not empty in response"

    
    def test_delete_already_deleted_bucket(self, storage, existing_bucket):
        """
        Validate deletion of a bucket that has been previously deleted
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Delete bucket
        storage.delete_bucket(existing_bucket)

        # Attempt to delete the same bucket again
        response = storage.delete_bucket(existing_bucket)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deletion failed", "Deletion of a previously removed bucket succeeded or there was a problem in response"
    

    def test_delete_already_deleted_object_is_idempotent(self, storage, bucket_with_object):
        """
        Validate deletion of an object that has been previously deleted is idempotent
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Delete existing object in a bucket
        storage.delete_object(bucket_with_object, OBJECT_KEY)

        # Attempt to delete the same object in the bucket
        response = storage.delete_object(bucket_with_object, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['bucket_name'] == bucket_with_object, "Deleted bucket name not in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"

    
    def test_delete_bucket_without_removing_its_objects(self, storage, bucket_with_object):
        """
        Validate correct response when attempting to delete a bucket without removing its objects
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        # Attempt to delete bucket with object in it
        response = storage.delete_bucket(bucket_with_object)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deletion failed", "Deletion of a bucket with objects succeeded or there was a problem in response"


    def test_upload_large_file_exceeding_limit(self, storage, existing_bucket):
        """
        Validate uploading a file that exceeds the multipart size limit (1 MB)
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        # Upload a large object (over 1 MB) to a bucket
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(LARGE_FILE_SIZE_LIMIT_EXEEDED))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object upload failed", "Upload succeeded, user shouldn't be able to upload a large file that exceeds the (1 MB) limit."


