import os
from app.storage_api.settings import settings

BUCKET = settings.minio_bucket_name
SECONDARY_BUCKET = "test-bucket2"
OBJECT_KEY = "sample.txt"
BASE_URL = os.getenv("S3_PUBLIC_ENDPOINT_URL", "http://127.0.0.1:9000")
