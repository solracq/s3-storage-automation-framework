# Test Plan:

## 1. Test Objectives
The objective of this testing is to verify and validate that the S3 implementation on the software backend works as expected and defined according to the user’s business requirements. 

Since the focus of the testing will be on the validation of the interaction with the backend of the software using the S3 implementation, the testing will involve API calls. Thus, the QA team will validate specifically the functional behaviour, the usability, the reliability, security and performance of the programming interface of the product.

## 2. Test Criteria
In this section, it is defined the different criteria to stop the test cycle or to stop the step to the next development cycle.

### 2.1. Stop Criteria
If the 40% of the test cases fail, the QA team will stop testing until the Dev team fixes the blocking issues.

### 2.2 Exit Criteria
If the 98% of all the test cases, including smoke and regression tests, pass; then, the QA team will be ready to sign-off the validation stage of the feature. 

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

## 5. Test Coverage
- Unit tests for framework utilities
- Smoke tests for service and bucket readiness
- Integration tests for upload/download/delete workflows
- Negative tests for missing objects, empty files, invalid credentials, and unavailable services
EOF

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

## 6. Schedule & Estimates
It is estimated to complete test design on the first sprint after feature complete. Then, test case execution can be performed in the following sprints. One sprint will be reserved for Automaiton testing. The potential release of the product it is scheduled in the next X months so the validation of the product is expected to be completed in X months.

## 7. Test Deliverables
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
