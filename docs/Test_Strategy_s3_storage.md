# Test Strategy:

## 1. Purpose
This test strategy defines the overall testing approach for the S3 Storage Automation Framework. It explains the scope, test levels, test types, environments, risks, tools, and quality practices used to validate a local S3-compatible storage workflow.

## 2. Test Scope
The validation of the interaction to the software using S3 SDK will require testing the software interface to the backend through API calls. Therefore, the scope of this testing is to validate the software API and the software backend of the product.

Since the focus of this S3-storage validation is on the backend, the validation of the User Interface of the software is out of scope.

#### What this validates
- Bucket creation/deletion
- Object upload/download/delete
- Metadata validation
- Object versioning, if enabled
- Presigned URL generation
- Negative cases: wrong credentials, missing bucket, missing object, invalid file type
- Storage quota simulation
- Retry behavior for temporary service unavailability
- Audit/log validation from container logs

## 3. System Specifications
For the system under test, we won't be using a formal AWS S3 Server. Instead, part of this project is to deploy an S3-compatible object storage service running locally.

#### System under test
- MinIO container (local S3-compatible without AWS IAM.)
- Small FastAPI wrapper service that uploads/downloads files to S3.
- Boto3 (AWS S3 SDK for Python) test client. Boto3 uses a custom non-AWS S3-compatible endpoint_url.

## 4. Roles
The Dev and QA teams will be involved on the product development and testing.
Carlos Quiroz - Software Developer Engineer in Test

## 5. Test Levels
- Unit Testing: Validates framework utilities and configuration helpers.
- Smoke Testing: Confirms MinIO, buckets, and service health are ready.
- Integration Testing: Validates upload, download, delete, metadata, and presigned URL workflows.
- Negative Testing: Validates expected failures for invalid credentials, missing buckets, missing objects, and unavailable services.
- Regression Testing: Re-runs core scenarios after framework or service changes.

## 6. Testing Types
The following testing types will be performed on verification and validation of the product.
- API Testing (Functional)
- Security Testing
- Reliability Testing
- Regression Testing
- API Documentation Testing

## 7. Risk Analysis
* Risk 1: S3 Server requires comprehensive configuration and maintenance 
    * Occurrence : Medium
    * Severity: High
    * Mitigation: Apply S3 Server maintenance once every month
* Risk 2: If S3 server access credentials get expired, access to the server and tests will fail.
    *  Occurrence : Medium
    * Severity: High
    * Mitigation:  Update S3 server credentials once every month
* Risk 3: Local storage limits may affect large-file test execution.
    * Occurrence : Medium
    * Severity: Medium
    * Mitigation: Use controlled test file sizes and document storage assumptions.
* Risk 4: Credentials may be exposed if environment files are committed.
    * Occurrence : Low
    * Severity: High
    * Mitigation: Store credentials in `.env`, exclude `.env` from Git, and provide `.env.example`.

## 8. Automation Strategy
Automated tests will be written in Python using Pytest. Tests will be grouped by purpose:
- `tests/unit/`
- `tests/smoke/`
- `tests/integration/`
- `tests/negative/`

Reusable S3 operations will be implemented in framework helper modules to avoid duplication and improve maintainability.

## 9. CI/CD Strategy
The project can be integrated with GitHub Actions to run linting and automated tests on pull requests or commits to the main branch. For local dependency tests, Docker will be used to start MinIO before test execution.

## 10. Test Logistics
The validation of the product in matter will be performed by one SDET on the next sprint after feature is completed. So, it is required that the test requirements, S3 like-server and SDET to be available in order to start testing.
