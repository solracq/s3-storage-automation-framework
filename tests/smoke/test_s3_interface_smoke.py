import pytest
from uuid import uuid4

from src.storage_automation import s3_client as s3_client_module
from src.storage_automation import s3_resource as s3_resource_module
from src.storage_automation.s3_client import S3Client
from src.storage_automation.s3_resource import S3Resource
from tests.utils.constants import BASE_URL, BUCKET, SECONDARY_BUCKET, OBJECT_KEY, CONTENT_DATA, FILE_PATH


pytestmark = pytest.mark.smoke


# Fixtures

@pytest.fixture(
    params=[
        ("client", s3_client_module, S3Client),
        ("resource", s3_resource_module, S3Resource),
    ],
    ids=["client", "resource"],
)
def storage(request, monkeypatch):
    _, module, s3_cls = request.param
    monkeypatch.setattr(module.settings, "s3_endpoint_url", BASE_URL)
    return s3_cls()


@pytest.fixture
def bucket_name(storage):
    """
    Provide a unique bucket name per test and always attempt cleanup.
    """
    name = f"{BUCKET}-{uuid4().hex[:8]}"
    yield name

    buckets_response = storage.list_buckets()
    if "Buckets" not in buckets_response:
        pytest.fail(f"Teardown could not verify bucket cleanup for '{name}': {buckets_response}")

    bucket_exists = any(bucket["Name"] == name for bucket in buckets_response["Buckets"])
    if not bucket_exists:
        return

    for obj in storage.list_objects(name):
        delete_object_response = storage.delete_object(name, obj["key"])
        if delete_object_response.get("message") != "Object deleted successfully":
            pytest.fail(
                f"Teardown failed to delete object '{obj['key']}' from bucket '{name}': "
                f"{delete_object_response}"
            )

    delete_bucket_response = storage.delete_bucket(name)
    if delete_bucket_response.get("message") != "Bucket deleted successfully":
        pytest.fail(f"Teardown failed to delete bucket '{name}': {delete_bucket_response}")


@pytest.fixture
def existing_bucket(storage, bucket_name):
    """
    Create a bucket for tests that need an existing bucket.
    """
    response = storage.create_bucket(bucket_name)
    assert response["message"] == "Bucket created successfully"
    return bucket_name


@pytest.fixture
def bucket_with_object(storage, existing_bucket):
    """
    Create a bucket and upload a fixture object for object-level smoke tests.
    """
    response = storage.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))
    assert response["message"] == "Object uploaded successfully"
    return existing_bucket


# Tests

class TestS3InterfaceSmoke:
    def test_create_bucket(self, storage, bucket_name):
        """
        Validate creation of a bucket
        Args:
            storage: s3 storage (client or resource) object
            bucket_name: unique bucket name for the test
        """
        response = storage.create_bucket(bucket_name)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket created successfully", "Unsuccessful bucket creation in response"


    def test_delete_bucket(self, storage, existing_bucket):
        """
        Validate deletion of a bucket
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
        response = storage.delete_bucket(existing_bucket)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "Unsuccessful bucket deletion in response"


    def test_list_buckets(self, storage, existing_bucket):
        """
        Validate listing of bucket(s) using S3 resource
        Args:
            storage: s3 storage (client or resource) object
            existing_bucket: unique bucket already created for the test
        """
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
        response = storage.upload_object(existing_bucket, OBJECT_KEY, str(FILE_PATH))

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Object uploaded successfully", "Unsuccessful object upload in response"


    def test_list_objects(self, storage, bucket_with_object):
        """
        Validate listing objects in a bucket
        Args:
            storage: s3 storage (client or resource) object
            bucket_with_object: fixture to create a bucket and upload an object
        """
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
        response = storage.get_object_size(bucket_with_object, OBJECT_KEY)
        
        assert response > 0, "Object size must be bigger than zero"
