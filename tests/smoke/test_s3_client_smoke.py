import pytest

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
def initialize_bucket(s3_client):
    s3_client.create_bucket(BUCKET)
    yield
    s3_client.delete_object(BUCKET, OBJECT_KEY)
    s3_client.delete_bucket(BUCKET)


@pytest.fixture
def create_bucket_with_object(s3_client):
    s3_client.create_bucket(BUCKET)
    s3_client.upload_object(BUCKET, OBJECT_KEY, FILE_PATH)
    yield
    s3_client.delete_object(BUCKET, OBJECT_KEY)
    s3_client.delete_bucket(BUCKET)


# Tests

class TestS3ClientSmoke:
    def test_create_bucket(self, s3_client):
        """
        Validate creation of a bucket
        Args:
            s3_client: s3 client object
        """
        response = s3_client.create_bucket(BUCKET)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket created successfully", "Unsuccessful bucket creation in response"
        
        s3_client.delete_bucket(BUCKET)


    def test_delete_bucket(self, s3_client):
        """
        Validate deletion of a bucket
        Args:
            s3_client: s3 client object
        """
        s3_client.create_bucket(BUCKET)

        response = s3_client.delete_bucket(BUCKET)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"


    def test_list_buckets(self, s3_client, initialize_bucket):
        """
        Validate listing of bucket(s)
        Args:
            s3_client: s3 client object
        """
        response = s3_client.list_buckets()
        
        assert isinstance(response, dict), "Response must be of dictionary type"
        assert "Buckets" in response, "'Buckets' string missing in response"
        assert any(bucket["Name"] == BUCKET for bucket in response["Buckets"]), f"Bucket name '{BUCKET}' is missing in response"


    def test_upload_object(self, s3_client, initialize_bucket):
        """
        Validate uploading of an object onto a bucket
        Args:
            s3_client: s3 client object
            initialize_bucket: fixture to create and teardown a bucket
        """
        response = s3_client.upload_object(BUCKET, OBJECT_KEY, FILE_PATH)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"


    def test_list_objects(self, s3_client, create_bucket_with_object):
        """
        Validate listing objects in a bucket
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.list_objects(BUCKET)

        assert response[0]['key'] == OBJECT_KEY, "Object key is not available in response"
        assert int(response[0]['size']) > 0, "Object size is not available in response"
        assert response[0]['last_modified'], "Object 'last_modified' info is not available in response"
    
    
    def test_download_object(self, s3_client, create_bucket_with_object):
        """
        Validate download of an object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.download_object(BUCKET, OBJECT_KEY, FILE_PATH)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object downloaded successfully", "Unsuccessful object download in response"
    

    def test_write_object(self, s3_client, create_bucket_with_object):
        """
        Validate write data to an object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.write_object(BUCKET, OBJECT_KEY, CONTENT_DATA)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object written successfully", "Unsuccessful object write in response"


    def test_read_object(self, s3_client, create_bucket_with_object):
        """
        Validate read data from an object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        s3_client.write_object(BUCKET, OBJECT_KEY, CONTENT_DATA)
        response = s3_client.read_object(BUCKET, OBJECT_KEY)
        
        assert response == CONTENT_DATA, "Unsuccessful object write in response"

        
    def test_delete_object(self, s3_client, create_bucket_with_object):
        """
        Validate delete object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.delete_object(BUCKET, OBJECT_KEY)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object deleted successfully", "Unsuccessful object deletion in response"
        assert response['bucket_name'] == BUCKET, "Deleted bucket name not in response"
        assert response['object_key'] == OBJECT_KEY, "Deleted object_key not in response"


    def test_get_object_metadata(self, s3_client, create_bucket_with_object):
        """
        Validate object metadata from an object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.get_object_metadata(BUCKET, OBJECT_KEY)
    
        assert response['ResponseMetadata']['HTTPHeaders']['content-length'], "'content-length' missed in metadata"
        assert response['ResponseMetadata']['HTTPHeaders']['last-modified'], "'LastModified' missed in metadata"
        assert response['ResponseMetadata']['HTTPHeaders']['etag'], "'ETag' missed in metadata"
        assert response['ResponseMetadata']['HTTPHeaders']['content-type'], "'ContentType' missed in metadata"


    def test_get_object_size(self, s3_client, create_bucket_with_object):
        """
        Validate object size from an object
        Args:
            s3_client: s3 client object
            create_bucket_with_object: fixture to create a bucket and upload an object
        """
        response = s3_client.get_object_size(BUCKET, OBJECT_KEY)
        
        assert response > 0, "Object size must be bigger than zero"

