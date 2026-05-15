import os
from app.storage_api.settings import settings

BUCKET = settings.minio_bucket_name
SECONDARY_BUCKET = "test-bucket2"
OBJECT_KEY = "sample.txt"
BASE_URL = os.getenv("S3_PUBLIC_ENDPOINT_URL", "http://127.0.0.1:9000")
CONTENT_DATA = "Hello from the write_object endpoint"
FILE_PATH = "/Users/carlosquiroz/dev/s3-storage-automation-framework/docs/Postman_collection_run_files/sample.txt"
