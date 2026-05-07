# s3-storage-automation-framework

Amazon Simple Storage Service (Amazon S3) is an object storage service that provides high durability, availability and performance. Data can be accessed from anywhere via Internet, through Amazon Console and S3 API. S3 storage service stores data as objects within buckets. An object is a file and any metadata that describes the file. A bucket is a container for objects.

This test automation framework validates an S3-compatible object storage service running locally.

# System under test
* MinIO container
* Small FastAPI wrapper service that uploads/downloads files to S3
* Boto3 (AWS S3 SDK for Python) test client

# What this validates:
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
can_messages_automation/
├── configs/
│   └── test_environment.example.json
├── dbc/
├── docs/
│   └── STEP_BY_STEP.md
├── scripts/
│   └── setup_vcan.sh
├── src/
│   └── can_framework/
│       ├── __init__.py
│       ├── bus.py
│       ├── message.py
│       ├── simulated_ecu.py
│       └── validators.py
├── tests/
│   ├── conftest.py
│   ├── integration/
│   |   ├── simple_example.py
│   │   ├── test_vcan_loopback.py
|   |   └── test_simulated_ecu_reaction.py
│   ├── smoke/
│   │   └── test_framework_smoke.py
│   └── unit/
│       └── test_validators.py
├── pytest.ini
└── requirements.txt
```

## Quick start

```text
s3-storage-automation-framework/
├── app/
│   └── main.py    -> FastAPI service
├── framework/
│   ├── s3/
│   │    ├── s3_client.py  -> Reusable Boto3 wrapper
│   │    ├── s3_resource.py
│   └── utils/
│           └── helpers.py
├── tests/
│   ├── conftest.py    -> Fixtures (MinIO setup)
│   ├── unit/
│   ├── smoke/
│   └── integration/
├── pytest.ini
├── .gitignore
└── requirements.txt
```
