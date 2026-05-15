import pytest

from src.storage_automation import s3_client as s3_client_module
from src.storage_automation.s3_client import S3Client
from tests.utils.constants import BASE_URL, BUCKET, SECONDARY_BUCKET, OBJECT_KEY


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


# Tests

class TestS3ClientSmoke:
    def test_create_bucket(self, s3_client):
        response = s3_client.create_bucket(BUCKET)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket created successfully", "No successful bucket creation in response"
        
        s3_client.delete_bucket(BUCKET)


    def test_delete_bucket(self, s3_client):
        s3_client.create_bucket(BUCKET)

        response = s3_client.delete_bucket(BUCKET)

        assert isinstance(response, dict), "Response must be of dictionary type"
        assert response['message'] == "Bucket deleted successfully", "No successful bucket deletion in response"


    def test_list_buckets(self, s3_client, initialize_bucket):
        response = s3_client.list_buckets()
        
        assert isinstance(response, dict), "Response must be of dictionary type"
        assert "Buckets" in response, "'Buckets' string missing in response"
        assert any(bucket["Name"] == BUCKET for bucket in response["Buckets"]), f"Bucket name '{BUCKET}' is missing in response"
