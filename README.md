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
1. Build and start environment in a terminal and keep it open. This will star the 'portfolio-minio' and the 'portfolio-storage-api' services defined in the docker-composer.yml.
```text
docker compose up --build
```
If rebuilding:
```text
docker compose build --no-cache storage-api
docker compose up
```

2. Verify container is running:
docker ps

3. Open browser to see local services. Login with minioadmin / minioadmin123
```text
|     Service       |             URL            |
|-------------------|----------------------------|
|   FastAPI Service |   http://localhost:8000    |
|   MinIO S3 API    |   http://localhost:9000    |
| MinIO Web Console |   http://localhost:9001    |
```


4. Teardown services. The command below stops containers and delete MinIO sotored data
```text
   docker-compose down -v
```



