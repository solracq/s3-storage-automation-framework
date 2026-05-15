import pytest
from uuid import uuid4

from src.storage_automation import s3_client as s3_client_module
from src.storage_automation.s3_client import S3Client
from tests.utils.constants import BASE_URL, BUCKET, OBJECT_KEY, CONTENT_DATA, FILE_PATH


pytestmark = pytest.mark.smoke


# Fixtures

@pytest.fixture
def s3_client(monkeypatch):
    monkeypatch.setattr(s3_client_module.settings, "s3_endpoint_url", BASE_URL)
    monkeypatch.setattr(s3_client_module.settings, "aws_access_key_id", "minioadmin")
    monkeypatch.setattr(s3_client_module.settings, "aws_secret_access_key", "minioadmin123")
    return S3Client()


@pytest.fixture
def bucket_name(s3_client):
    """
    Provide a unique bucket name per test and always attempt cleanup.
    """
    name = f"{BUCKET}-{uuid4().hex[:8]}"
    yield name
    s3_client.delete_object(name, OBJECT_KEY)
    s3_client.delete_bucket(name)


@pytest.fixture
def existing_bucket(s3_client, bucket_name):
    """
    Create a bucket for tests that need an existing bucket.
    """
    response = s3_client.create_bucket(bucket_name)
    assert response["message"] == "Bucket created successfully"
    return bucket_name


@pytest.fixture
def bucket_with_object(s3_client, existing_bucket):
    """
    Create a bucket and upload a fixture object for object-level smoke tests.
    """
    response = s3_client.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))
    assert response["message"] == "Object uploaded successfully"
    return existing_bucket


# Tests

class TestS3ClientSmoke:
    def test_create_bucket(self, s3_client, bucket_name):
        """
        Validate creation of a bucket
        Args:
            s3_client: s3 client object
            bucket_name: unique bucket name for the test
        """
        response = s3_client.create_bucket(bucket_name)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket created successfully", "Unsuccessful bucket creation in response"


    def test_delete_bucket(self, s3_client, existing_bucket):
        """
        Validate deletion of a bucket
        Args:
            s3_client: s3 client object
            existing_bucket: unique bucket already created for the test
        """
        response = s3_client.delete_bucket(existing_bucket)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"


    def test_list_buckets(self, s3_client, existing_bucket):
        """
        Validate listing of bucket(s)
        Args:
            s3_client: s3 client object
            existing_bucket: unique bucket already created for the test
        """
        response = s3_client.list_buckets()
        
        assert isinstance(response, dict), "Response must be of dictionary type"
        assert "Buckets" in response, "'Buckets' string missing in response"
        assert any(bucket["Name"] == existing_bucket for bucket in response["Buckets"]), f"Bucket name '{existing_bucket}' is missing in response"


    def test_upload_object(self, s3_client, existing_bucket):
        """
        Validate uploading of an object onto a bucket
        Args:
            s3_client: s3 client object
            existing_bucket: unique bucket already created for the test
        """
        response = s3_client.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"


    def test_list_objects(self, s3_client, bucket_with_object):
        """
        Validate listing objects in a bucket
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.list_objects(bucket_with_object)

        assert response[0]['key'] == OBJECT_KEY, "Object key is not available in response"
        assert int(response[0]['size']) > 0, "Object size is not available in response"
        assert response[0]['last_modified'], "Object 'last_modified' info is not available in response"
    
    
    def test_download_object(self, s3_client, bucket_with_object, tmp_path):
        """
        Validate download of an object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
            tmp_path: pytest temporary directory for downloaded files
        """
        download_path = tmp_path / OBJECT_KEY
        response = s3_client.download_object(bucket_with_object, OBJECT_KEY, str(download_path))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object downloaded successfully", "Unsuccessful object download in response"
        assert download_path.exists(), "Downloaded file was not created"
        assert download_path.read_bytes() == FILE_PATH.read_bytes(), "Downloaded object content does not match source fixture data"
    

    def test_write_object(self, s3_client, bucket_with_object):
        """
        Validate write data to an object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        stored_content = s3_client.read_object(bucket_with_object, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object written successfully", "Unsuccessful object write in response"
        assert stored_content == CONTENT_DATA, "Written object content was not persisted correctly"


    def test_read_object(self, s3_client, bucket_with_object):
        """
        Validate read data from an object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        s3_client.write_object(bucket_with_object, OBJECT_KEY, CONTENT_DATA)
        response = s3_client.read_object(bucket_with_object, OBJECT_KEY)
        
        assert response == CONTENT_DATA, "Unsuccessful object write in response"

        
    def test_delete_object(self, s3_client, bucket_with_object):
        """
        Validate delete object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.delete_object(bucket_with_object, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['bucket_name'] == bucket_with_object, "Deleted bucket name not in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"


    def test_get_object_metadata(self, s3_client, bucket_with_object):
        """
        Validate object metadata from an object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.get_object_metadata(bucket_with_object, OBJECT_KEY)
    
        assert response["ContentLength"] > 0, "'ContentLength' missed in metadata"
        assert response["LastModified"], "'LastModified' missed in metadata"
        assert response["ETag"], "'ETag' missed in metadata"
        assert response["ContentType"], "'ContentType' missed in metadata"


    def test_get_object_size(self, s3_client, bucket_with_object):
        """
        Validate object size from an object
        Args:
            s3_client: s3 client object
            bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.get_object_size(bucket_with_object, OBJECT_KEY)
        
        assert response > 0, "Object size must be bigger than zero"
