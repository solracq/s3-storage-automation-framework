# Test Strategy:

## 1. Test Scope
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

### 1.1 Test Specifications
For the system under test, we won't be using a formal AWS S3 Server. Instead, part of this project is to deploy an S3-compatible object storage service running locally.

#### System under test
- MinIO container (local S3-compatible without AWS IAM.)
- Small FastAPI wrapper service that uploads/downloads files to S3.
- Boto3 (AWS S3 SDK for Python) test client. Boto3 uses a custom non-AWS S3-compatible endpoint_url.

### 1.2 Roles
The Dev and QA teams will be involved on the product development and testing.
Carlos Quiroz - Software Developer Engineer in Test

## 2. Testing Types
The following testing types will be performed on verification and validation of the product.
- API Testing (Functional)
- Security Testing
- Usability Testing
- Reliability Testing
- Regression Testing
- API Documentation Testing
- Interoperablity Testing

## 3. Risk Analysis
* Risk 1: S3 Server requires comprehensive configuration and maintenance 
    * Occurrence : Medium
    * Severity: High
    * Mitigation: Apply S3 Server maintenance once every month
* Risk 2: If S3 server access credentials get expired, access to the server and tests will fail.
    *  Occurrence : Medium
    * Severity: High
    * Mitigation:  Update S3 server credentials once every month
* Risk 3: Server storage constrains will affect test results
    * Occurrence : Medium
    * Severity: High
    * Mitigation: Deploy S3 server into a VM/HCP server with larger storage (>1T)
* Risk 4: Access and Secret Keys need to be shared in all test environments to have the tests fully working
    * Occurrence : Low
    * Severity: Medium
    * Mitigation: Update config files every release

## 4. Test Logistics
The validation of the product in matter will be performed by one SDET on the next sprint after feature is completed. So, it is required that the test requirements, S3 like-server and SDET to be available in order to start testing.
