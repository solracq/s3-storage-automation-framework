# s3-storage-automation-framework

Amazon Simple Storage Service (Amazon S3) is an object storage service that provides high durability, availability and performance. Data can be accessed from anywhere via Internet, through Amazon Console and S3 API. S3 storage service stores data as objects within buckets. An object is a file and any metadata that describes the file. A bucket is a container for objects.

This test automation framework validates an S3-compatible object storage service running locally.

## System under test
* MinIO container (local S3-compatible without AWS IAM.)
* Small FastAPI wrapper service that uploads/downloads files to S3.
* Boto3 (AWS S3 SDK for Python) test client. Boto3 uses a custom non-AWS S3-compatible endpoint_url.

## What this validates:
- Bucket creation/deletion
- Object upload/download/delete
- Metadata validation
- Object versioning, if enabled
- Presigned URL generation
- Negative cases: wrong credentials, missing bucket, missing object, invalid file type
- Storage quota simulation
- Retry behavior for temporary service unavailability
- Audit/log validation from container logs

## Initial folder structure

```text
s3_storage_automation/
├── app/
│   └── storage_api/
│       ├── main.py
│       ├── settings.py
│       └── Dockerfile
├── s3_lib/
│   ├── __init__.py
│   ├── s3/
│   │   ├── __init__.py
│   │   ├── s3_client.py
│   │   └── s3_resource.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── smoke/
│   └── integration/
├── scripts/
├── docs/
├── .env
├── .gitignore
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

## Environment Setup
1. MinIO S3-compatible storage in Docker.
2. FastAPI wrapper service that uploads/downloads files to MinIO.
3. Manual validation using curl to test setup works well.

### Launch MinIO with Docker
1. Start docker container
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  quay.io/minio/minio server /data --console-address ":9001"

2. Verify container is running:
docker ps

3. Open browser to see the MinIO web console, http://localhost:9001
Login with minioadmin / minioadmin123


