# s3-storage-automation-framework

Amazon Simple Storage Service (Amazon S3) is an object storage service that provides high durability, availability and performance. Data can be accessed from anywhere via Internet, through Amazon Console and S3 API. S3 storage service stores data as objects within buckets. An object is a file and any metadata that describes the file. A bucket is a container for objects.

This test automation framework validates an S3-compatible object storage service running locally.

## FastAPI wrapper service
The FastAPI wrapper service provides a small HTTP layer over the S3 operations implemented in the storage automation code. It uses `boto3` to talk to MinIO, which is running locally as an S3-compatible object storage service.

In this project, MinIO acts as the system under test, while the FastAPI app acts as a simple test-facing adapter. That wrapper makes it easier to validate bucket and object operations with `curl`, browser-based docs, and later automated API tests without having to call the S3 SDK directly every time.

## S3 client vs resource implementations
This project keeps both `s3_client.py` and `s3_resource.py` on purpose so the same MinIO-backed scenarios can be exercised through the two main `boto3` access styles.

- `s3_client.py` uses `boto3.client("s3")`, which is the lower-level SDK interface. It stays close to the raw S3 API, returns dictionary-shaped responses, and is useful when the test needs explicit request/response handling that mirrors the wire-level operations.
- `s3_resource.py` uses `boto3.resource("s3")`, which is the higher-level, object-oriented SDK interface. It exposes helpers such as `Bucket` and `Object`, and is useful when the test benefits from more readable bucket/object interactions.

Keeping both implementations in the repository makes it easier to compare low-level and high-level S3 calls against the same storage service, and to document where a resource abstraction is convenient versus where a client-style dictionary response is a better fit.

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
├── src/
│   ├── __init__.py
│   ├── storage_automation/
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── s3.py
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

## Postman Setup
Before running the exported Postman collection, set Postman's working directory to the root of this repository so file-based requests can resolve correctly.

1. Open the Postman desktop app.
2. Click the gear icon and open `Settings`.
3. Go to the `General` tab.
4. Find the `Working directory` setting.
5. Click `Choose` or `Change`.
6. Select the root folder of this repository.
Example:
```text
/path/to/s3-storage-automation-framework
```
1. Save or close settings.
2. Re-open the collection and verify the file-based requests reference files under:
```text
docs/Postman_collection_run_files/
```

Expected test asset files:
```text
docs/Postman_collection_run_files/sample.txt
docs/Postman_collection_run_files/empty-sample.txt
docs/Postman_collection_run_files/large-sample.txt
docs/Postman_collection_run_files/image.png
docs/Postman_collection_run_files/non-ascii-sample.txt
```

## API Endpoints
- `GET /health` : service health check
- `POST /buckets/bootstrap?bucket_name=...` : ensure a bucket exists
- `POST /buckets?bucket_name=...` : create a bucket
- `DELETE /buckets/{bucket_name}` : delete a bucket
- `GET /buckets` : list buckets
- `POST /files/{object_key}` : upload a file to the default configured bucket
- `GET /files?bucket_name=...` : list objects in a bucket
- `GET /files/{object_key}` : download a file from the default configured bucket
- `DELETE /files/{object_key}?bucket_name=...` : delete an object from a bucket
- `GET /objects/{object_key}/metadata?bucket_name=...` : get object metadata
- `GET /objects/{object_key}/size?bucket_name=...` : get object size
- `PUT /objects/{object_key}?bucket_name=...` : write raw object content
- `GET /objects/{object_key}?bucket_name=...` : read raw object content

**Note:** FastAPI also exposes interactive API docs at `http://localhost:8000/docs` and `http://localhost:8000/redoc`.

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

4. Teardown services. The command below stops containers and delete 
Stop containers but keep MinIO data:
```text
   docker-compose down
```
Stop containers and delete MinIO stored data:
```text
   docker-compose down -v
```

### Validate the FastAPI service manually using curl
On a different terminal run:
```text
curl http://localhost:8000/health
```
Result:
```text
{
  "status": "ok",
  "service": "storage-api"
}
```

```text
curl -X POST "http://localhost:8000/buckets/bootstrap?bucket_name=test-bucket"
```
Result:
```text
{"bucket":"test-bucket","status":"ready"}
```
```text
curl "http://localhost:8000/files?bucket_name=test-bucket"
```
Result:
```text
{"bucket":"test-bucket","objects":[]}
```
**Note:** For a more complete manual validation flow and additional `curl` examples, see [docs/Exploratory_Testing.md](docs/Exploratory_Testing.md).

## Automated Tests

### Running Unit Test Suite
```text
./s3venv/bin/pytest tests/unit -q
./s3venv/bin/pytest tests/unit/test_s3_client.py -q
./s3venv/bin/pytest tests/unit/test_s3_resource.py -q
```
**Running unit tests only for the S3 Client implementation**
```text
./s3venv/bin/pytest tests/unit/test_s3_client.py -q
```

**Running unt tests only for the S3 Resource implementation**
```text
./s3venv/bin/pytest tests/unit/test_s3_resource.py -q
```

### Running Smoke Test Suite
```text
pytest -v -m smoke -s
```

