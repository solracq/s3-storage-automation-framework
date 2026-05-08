# Test Plan:

## 1. Test Objectives
The objective of this testing is to verify and validate that the S3 implementation on the software backend works as expected and defined according to the user’s business requirements. 

Since the focus of the testing will be on the validation of the interaction with the backend of the software using the S3 implementation, the testing will involve API calls. Thus, the QA team will validate specifically the functional behaviour, the usability, the reliability, security and performance of the programming interface of the product.

## 2. Entry, Suspension, and Exit Criteria
In this section, it is defined the different testing criteria.

### 2.1 Entry Criteria
- MinIO container is running.
- FastAPI service is available.
- Required environment variables are configured.
- Test data and sample files are available.
- Smoke tests can be executed locally.

### 2.2 Suspension Criteria
- More than 40% of critical test cases fail.
- The API service is unavailable.
- MinIO cannot be reached.
- Test credentials are invalid or missing.

### 2.3 Exit Criteria
- 98% of planned test cases pass.
- All critical and high-severity defects are resolved or accepted.
- Smoke and regression tests pass.
- Test results are documented.

## 3. Test Resources
The validation of the feature will require the following resources:
* One SDET
* S3 like-server (local S3-compatible without AWS IAM)
* Boto3 (AWS SDK for Python)
* Python
* Pytest
* Docker (MinIO container)
* FastAPI wrapper service

## 4. Test Environment
The installation of the software will require the following:
* MacOS
* AWS S3 SDK
* MinIO container (local S3-compatible without AWS IAM.)
* Small FastAPI wrapper service that uploads/downloads files to S3.
* Python modules:
    - fastapi
    - uvicorn
    - boto3
    - python-dotenv
    - pytest
    - pytest-asyncio
    - httpx
    - requests

## 5. Scope

### In Scope
- API validation for upload, download, delete, metadata, and presigned URLs.
- MinIO bucket readiness and object storage workflows.
- Negative testing for missing buckets, missing objects, invalid credentials, and service unavailability.
- Basic performance and reliability validation.

### Out of Scope
- AWS IAM validation.
- Real AWS S3 billing, replication, lifecycle policies, and multi-region behavior.
- Frontend/UI testing.

## 6. Test Coverage
- Unit tests for framework utilities
- Smoke tests for service and bucket readiness
- Integration tests for upload/download/delete workflows
- Negative tests for missing objects, empty files, invalid credentials, and unavailable services

### Test Scenarios
tests/unit/
  test_file_factory.py
  test_config_loader.py

tests/smoke/
  test_minio_health.py
  test_bucket_create_delete.py

tests/integration/
  test_upload_download_object.py
  test_object_metadata.py
  test_presigned_url.py

tests/negative/
  test_invalid_credentials.py
  test_missing_bucket.py
  test_missing_object.py

### Test Data
The test suite will use:
- Small text files
- Empty files
- Files with metadata
- Unsupported file types, if validation exists
- Large files for basic upload/download validation
- Missing object keys for negative scenarios

### Defect Management
Defects will be documented using GitHub Issues. Each defect should include:
- Summary
- Steps to reproduce
- Expected result
- Actual result
- Severity
- Logs or screenshots, if applicable

## 9. Schedule & Estimates
This project is planned as a personal automation framework. Test design, implementation, and execution will be completed iteratively as framework features are added.

Estimated phases:
- Phase 1: Environment setup and smoke tests
- Phase 2: Core API workflow tests
- Phase 3: Negative and reliability tests
- Phase 4: Regression execution and documentation

## 10. Test Deliverables
* Before testing:
    * Test plan
    * Test strategy
    * README about details of the S3-like server deployment
* During testing:
    * Test cases
    * Automated tests
    * Automation framework
    * Logs
    * Bug reports
* After testing:
    * Test Results
    * Release notes
