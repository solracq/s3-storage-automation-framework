# Exploratory Test Document:

## Purpose
Document to show the initial manual testing activity to understand and validate the product.

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

## Notes
- Quote URLs that contain query parameters when using `zsh`, for example: `curl "http://localhost:8000/files?bucket_name=test-bucket"`.
- The `/files/{object_key}` routes use the default configured bucket, while the `/objects/...` routes require an explicit `bucket_name` query parameter.

## Postman Setup
Before running the exported Postman collection, set Postman's working directory to the root of this repository so file-based requests can resolve correctly.

1. Open the Postman desktop app.
2. Open `Settings`.
3. Go to `General`.
4. Set `Working directory` to the repository root.
Example:
```text
/path/to/s3-storage-automation-framework
```
5. Verify file-based requests point to files under:
```text
tests/data/
```

Expected test asset files:
```text
docs/Postman_collection_run_files/sample.txt
docs/Postman_collection_run_files/empty-sample.txt
docs/Postman_collection_run_files/large-sample.txt
docs/Postman_collection_run_files/image.png
docs/Postman_collection_run_files/non-ascii-sample.txt
```

## Test Scenarios

### Positive Scenarios
#### Scenario 1: Check FastAPI health
```text
curl http://localhost:8000/health
```

**Expected**
status: ok

**Output**
```text
portfolio-storage-api  | INFO:  "GET /health HTTP/1.1" 200 OK
{"status":"ok","service":"storage-api"}
```

#### Scenario 2: Bootstrap the S3 bucket
```text
curl -X POST "http://localhost:8000/buckets/bootstrap?bucket_name=test-bucket"
```

**Expected**
status: ready

**Output**
```text
portfolio-storage-api  | INFO:  - "POST /buckets/bootstrap?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","status":"ready"}
```

#### Scenario 3: Bootstrap an already existing bucket and verify endpoint is idempotent
**Pre-conditions:**
- A bucket exists with the name "test-bucket"

**Bootstrap an S3 bucket with the same name as the existing one**
```text
curl -X POST "http://localhost:8000/buckets/bootstrap?bucket_name=test-bucket"
```

**Expected**
No new bucket gets created

**Output**
```text
portfolio-storage-api  | INFO:  - "POST /buckets/bootstrap?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","status":"ready"}
```

##### Scenario 4: Upload a file
**Pre-conditions:**
A bucket has been created and a file is available locally

**Upload a file**
```text
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt
```

**Expected**
Object uploaded successfully

**Output**
```text
portfolio-storage-api  | INFO: - "POST /files/sample.txt HTTP/1.1" 200 OK

{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"sample.txt","content_type":"text/plain"}
```

##### Scenario 5: list files in bucket
**Pre-conditions:**
A bucket has been created and a file is available locally

**Upload a file**
```text
curl "http://localhost:8000/files?bucket_name=test-bucket"
```

**Expected**
bucket object(s) listed

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","objects":[{"key":"sample.txt","size":47,"last_modified":"2026-05-13T03:35:45.022000+00:00"}]}
```

##### Scenario 6: Download a file from a bucket
**Pre-conditions:**
A bucket has been created and contains a file

```text
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt
```

**Expected**
File is downloaded successfully and its content matches the uploaded file

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files/sample.txt HTTP/1.1" 200 OK

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    47  100    47    0     0   3523      0 --:--:-- --:--:-- --:--:--  3615
```

##### Scenario 7: Delete a file from bucket
**Pre-conditions:**
A bucket has been created and contains a file

```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**Expected**
Object deleted successfully

**Output**
```text
portfolio-storage-api  | INFO: - "DELETE /files/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}
```

#### Scenario 8: Create bucket
```text
curl -X POST "http://localhost:8000/buckets?bucket_name=test-bucket"
```

**Expected**
Bucket created successfully

**Output**
```text
INFO:   <client-ip>:<port>  - "POST /buckets?bucket_name=test-bucket2 HTTP/1.1" 200 OK
{"message":"Bucket created successfully"}
```

#### Scenario 9: List buckets
```text
curl "http://localhost:8000/buckets"
```

**Expected**
"Buckets":[
    {"Name":"test-bucket","CreationDate":"2026-05-13T01:07:36.480000+00:00"},
    {"Name":"test-bucket2","CreationDate":"2026-05-13T15:32:17.234000+00:00"}
    ]

**Output**
```text
INFO:   <client-ip>:<port> - "GET /buckets HTTP/1.1" 200 OK
{"ResponseMetadata":{"RequestId":"18AF29E9B45D9B90","HostId":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","HTTPStatusCode":200,"HTTPHeaders":{"accept-ranges":"bytes","content-length":"464","content-type":"application/xml","server":"MinIO","strict-transport-security":"max-age=31536000; includeSubDomains","vary":"Origin, Accept-Encoding","x-amz-id-2":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","x-amz-request-id":"18AF29E9B45D9B90","x-content-type-options":"nosniff","x-ratelimit-limit":"4278","x-ratelimit-remaining":"4278","x-xss-protection":"1; mode=block","date":"Wed, 13 May 2026 15:34:21 GMT"},"RetryAttempts":0},"Buckets":[{"Name":"test-bucket","CreationDate":"2026-05-13T01:07:36.480000+00:00"},{"Name":"test-bucket2","CreationDate":"2026-05-13T15:32:17.234000+00:00"}],"Owner":{"DisplayName":"minio","ID":"02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855f66bdbf4"}}
```

#### Scenario 10: Delete a bucket with objects by deleting objects first
**pre-conditions**
- Existing bucket contains one or more objects

**1. Delete Object(s) in bucket**
```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**2. Delete bucket**
```text
curl -X DELETE "http://localhost:8000/buckets/test-bucket"
```

**Expected**
Bucket deleted successfully

**Output**
```text
INFO:   <client-ip>:<port> - "DELETE /buckets/test-bucket2 HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}

{"message":"Bucket deleted successfully"}
```

#### Scenario 11: Get Object Metadata
**Pre-conditions**
A bucket exists with an object stored

```text
curl "http://localhost:8000/objects/sample.txt/metadata?bucket_name=test-bucket"
```

**Expected**
* Response metadata:
  - boto3/AWS SDK request info
* System object metadata should contain the following: 
  - LastModified
  - ContentLength
  - ETag
  - ContentType
* User-defined object metadata, if custom metadata sent with request (e.g. Metadata= {"source": "curl",})
  - Metadata: {}

**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/sample.txt/metadata?bucket_name=test-bucket HTTP/1.1" 200 O

{"ResponseMetadata":{"RequestId":"18AF2B7065A201D4","HostId":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","HTTPStatusCode":200,"HTTPHeaders":{"accept-ranges":"bytes","content-length":"47","content-type":"text/plain","etag":"\"ce52118d5f6333dbb5d7ebd0a1fc6893\"","last-modified":"Wed, 13 May 2026 16:01:30 GMT","server":"MinIO","strict-transport-security":"max-age=31536000; includeSubDomains","vary":"Origin, Accept-Encoding","x-amz-id-2":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","x-amz-request-id":"18AF2B7065A201D4","x-content-type-options":"nosniff","x-ratelimit-limit":"4278","x-ratelimit-remaining":"4278","x-xss-protection":"1; mode=block","date":"Wed, 13 May 2026 16:02:19 GMT"},"RetryAttempts":0},"AcceptRanges":"bytes","LastModified":"2026-05-13T16:01:30+00:00","ContentLength":47,"ETag":"\"ce52118d5f6333dbb5d7ebd0a1fc6893\"","ContentType":"text/plain","Metadata":{}}
```

#### Scenario 12: Get Object Size
**Pre-conditions**
A bucket exists with one object/file

```text
curl "http://localhost:8000/objects/sample.txt/size?bucket_name=test-bucket"
```
**Expected**
bucket object size is shown


**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/sample.txt/size?bucket_name=test-bucket HTTP/1.1" 200 OK
{"bucket_name":"test-bucket","object_key":"sample.txt","size":47}
```

#### Scenario 13: Write Object
**Pre-conditions**
A bucket exists with one object/file

**1. Write content from local file**
```text
curl -X PUT "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" --data-binary @sample.txt
```

**2. Write literal text directly**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  -H "Content-Type: text/plain" \
  --data-binary 'Hello from the write_object endpoint'
```

**3. Write multiple lines directly**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  --data-binary $'Hello from write_object\nThis is line 2\nThis is line 3'
```

**Expected**
Object content is overwritten with the provided request body

**Output**
```text
INFO:   <client-ip>:<port> - "PUT /objects/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object written successfully"}
```

#### Scenario 14: Read Object
**Pre-conditions**
A bucket exists with one object/file with data

```text
curl "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket"
```

**Expected**
Data stored in object is displayed

**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

Hello from the write_object endpoint
```


### Negative Scenarios
#### Scenario 15: Create a bucket with an existing bucket name
**Pre-conditions:**
- An existing bucket exist with the name "test-bucket"

**Create a bucket with the "test-bucket" name**
```text
curl -X POST "http://localhost:8000/buckets?bucket_name=test-bucket"
```

**Expected**
Bucket creation failed... Your previous request to create the named bucket succeeded and you already own it.

**Output**
```text
INFO:   <client-ip>:<port> - "POST /buckets?bucket_name=test-bucket HTTP/1.1" 200 OK
Bucket creation failed: An error occurred (BucketAlreadyOwnedByYou) when calling the CreateBucket operation: Your previous request to create the named bucket succeeded and you already own it.

{"message":"Bucket creation failed","bucket_name":"test-bucket","error":"An error occurred (BucketAlreadyOwnedByYou) when calling the CreateBucket operation: Your previous request to create the named bucket succeeded and you already own it."}
```

#### Scenario 16: List an empty list of buckets
**Pre-conditions:**
- No buckets available in the storage server

**List buckets**
```text
curl "http://localhost:8000/buckets"
```

**Expected**
"Buckets":[]

**Output**
```text
INFO:  <client-ip>:<port>  - "GET /buckets HTTP/1.1" 200 OK

{"ResponseMetadata":{"RequestId":"18AF2A6A41897D60","HostId":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","HTTPStatusCode":200,"HTTPHeaders":{"accept-ranges":"bytes","content-length":"275","content-type":"application/xml","server":"MinIO","strict-transport-security":"max-age=31536000; includeSubDomains","vary":"Origin, Accept-Encoding","x-amz-id-2":"dd9025bab4ad464b049177c95eb6ebf374d3b3fd1af9251148b658df7ac2e3e8","x-amz-request-id":"18AF2A6A41897D60","x-content-type-options":"nosniff","x-ratelimit-limit":"4278","x-ratelimit-remaining":"4278","x-xss-protection":"1; mode=block","date":"Wed, 13 May 2026 15:43:33 GMT"},"RetryAttempts":0},"Buckets":[],"Owner":{"DisplayName":"minio","ID":"02d6176db174dc93cb1b899f7c6078f08654445fe8cf1b6ce98d8855f66bdbf4"}}
```

#### Scenario 17: Delete an already deleted bucket
**Pre-conditions:**
- "test-bucket2" has been previously deleted

**Attempt to delete already deleted bucket**
```text
curl -X DELETE "http://localhost:8000/buckets/test-bucket2"
```

**Expected**
Bucket deletion failed

**Output**
```text
INFO:   <client-ip>:<port> - "DELETE /buckets/test-bucket2 HTTP/1.1" 200 OK
Bucket deletion failed: test-bucket2

{"message":"Bucket deletion failed"}
```

##### Scenario 18: Delete an already deleted object in bucket
**Pre-conditions:**
- Bucket exists with no object

```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**Expected**
API treats deletion of missing object as success. S3 deletes are idempotent.

**Output**
```text
INFO:   <client-ip>:<port> - "DELETE /files/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}
```

#### Scenario 19: Delete a bucket with objects in it
**Pre-conditions:**
- bucket contains one or more objects

**Attempt to delete bucket**
```text
curl -X DELETE "http://localhost:8000/buckets/test-bucket"
```

**Expected**
Bucket deletion failed

**Output**
```text
INFO:   <client-ip>:<port> - "DELETE /buckets/test-bucket HTTP/1.1" 200 OK
{"message":"Bucket deletion failed"}
```

#### Scenario 20: Upload a file that exceeds the multipart size limit
**Description**
Implementation multipart parser defaults to max_part_size = 1024 * 1024 (1 MB)

**Pre-conditions:**
- An existing bucket exist with the name "test-bucket"

**1. Upload a large file (~1.7MB)**
```text
curl -X POST \
  -F "file=@large-sample.txt" \
  http://localhost:8000/files/large-sample.txt
```

**Expected**
User shouldn't be able to upload a large file that exceeds the limit.

**Output**
```text
INFO:    <client-ip>:<port> - "POST /files/large-sample.txt HTTP/1.1" 400 Bad Request

{"detail":"There was an error parsing the body"}
```

#### Scenario 21: Upload an empty file to a bucket
Note: This scenario requires two tests, one at the s3 implementation and other at the HTTP API level to show specific distinctive expected behaivour on each layer.

**Pre-conditions:**
- An existing bucket exist with the name "test-bucket"

**1. Upload a file with no data (0 bytes)**
```text
curl -X POST \
  -F "file=@empty-sample.txt" \
  http://localhost:8000/files/empty-sample.txt
```

**Expected**
File content cannot be empty

**Output**
```text
INFO:   <client-ip>:<port> - "POST /files/empty-sample.txt HTTP/1.1" 400 Bad Request

{"detail":"File content cannot be empty"}
```

##### Scenario 22: Call any endpoint that require `bucket_name` without the query param
** Pre-conditions
- A bucket exists with an object

**1. List bucket objects without providing `bucket_name` parameter
```text
curl "http://localhost:8000/files"
```

**Expected**
422 Unprocessable Entity returned
Field required message

**Output**
```text
INFO:   <client-ip>:<port> - "GET /files HTTP/1.1" 422 Unprocessable Entity

{"detail":[{"type":"missing","loc":["query","bucket_name"],"msg":"Field required","input":null}]}
```

##### Scenario 23: Send an upload request without the multipart file field
```text
curl -X POST http://localhost:8000/files/sample.txt
```

**Expected**
422 Unprocessable Entity returned
Field required message

**Output**
```text
INFO:   <client-ip>:<port> - "POST /files/sample.txt HTTP/1.1" 422 Unprocessable Entity

{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}
```

##### Scenario 24: Download object for a missing object in bucket
- A bucket exists with no objects stored in it

**Download the file**
```text
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt
```

**Expected**
404 Not Found

**Output**
```text
INFO:   <client-ip>:<port> - "GET /files/sample.txt HTTP/1.1" 404 Not Found
Object download failed: An error occurred (NoSuchKey) when calling the GetObject operation: The specified key does not exist.

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    41  100    41    0     0   3026      0 --:--:-- --:--:-- --:--:--  3153
```

#### Scenario 25: Create bucket with invalid name
```text
curl -X POST "http://localhost:8000/buckets?bucket_name=TEST-b@ck3t"
```

**Expected**
Parameter validation failed
Bucket with invalid name cannot be created

**Output**
```text
botocore.exceptions.ParamValidationError: Parameter validation failed:
portfolio-storage-api  | Invalid bucket name "TEST-b@ck3t": Bucket name must match the regex "^[a-zA-Z0-9.\-_]{1,255}$" or be an ARN matching the regex "^arn:(aws).*:(s3|s3-object-lambda):[a-z\-0-9]*:[0-9]{12}:accesspoint[/:][a-zA-Z0-9\-.]{1,63}$|^arn:(aws).*:s3-outposts:[a-z\-0-9]+:[0-9]{12}:outpost[/:][a-zA-Z0-9\-]{1,63}[/:]accesspoint[/:][a-zA-Z0-9\-]{1,63}$"

Internal Server Error
```

#### Scenario 26: Write Object with empty data
**Pre-conditions**
A bucket exists with one object/file

**1. Write emptycontent**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  -H "Content-Type: text/plain" \
  --data-binary ''
```

**Expected**
400 Bad Request
Request body cannot be empty

**Output**
```text
INFO:     172.27.0.1:56260 - "PUT /objects/sample.txt?bucket_name=test-bucket HTTP/1.1" 400 Bad Request

{"detail":"Request body cannot be empty"}
```


### Edge Scenarios

#### Scenario 27: Upload a large file within the limit to a bucket
**Description**
Implementation multipart parser defaults to max_part_size = 1024 * 1024 (1 MB)

**Pre-conditions:**
- A bucket exists with the name "test-bucket"

**1. Upload a large file (1MB)**
```text
curl -X POST \
  -F "file=@large-sample.txt" \
  http://localhost:8000/files/large-sample.txt
```

**Expected**
Object uploaded successfully

**Output**
```text
INFO:    <client-ip>:<port> - "POST /files/large-sample.txt HTTP/1.1" 200 OK

{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"large-sample.txt","content_type":"text/plain"}
```
#### Scenario 28: Upload an file containing non-ASCII characters and read object
**Pre-conditions:**
- An existing bucket exist with no object
- Local file with non-ASCII characteres

**1. Upload a file with non-ASCII characters**
```text
curl -X POST \
  -F "file=@non-ascii-sample.txt" \
  http://localhost:8000/files/non-ascii-sample.txt
```

**2. Read object**
```text
curl "http://localhost:8000/objects/non-ascii-sample.txt?bucket_name=test-bucket"
```

**Expected**
File content with non-ASCII characters can be read

**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/non-ascii-sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK
こんにちは！
```

### Integration Scenarios

#### Scenario 29: Delete recursively a bucket with empty file
```text
curl -X DELETE "http://localhost:8000/buckets/test-bucket2"
```

**Expected**
Bucket deleted successfully

**Output**
```text
INFO:   <client-ip>:<port> - "DELETE /buckets/test-bucket2 HTTP/1.1" 200 OK
{"message":"Bucket deleted successfully"}
```

##### Scenario 30: Upload an image then download it and compare checksums with `shasum -a 256`
**Pre-conditions:**
- A bucket exists with the name "test-bucket"
  
**Upload an image**
```text
curl -X POST \
  -F "file=@image.png" \
  http://localhost:8000/files/image.png
```
**Download the image**
```text
curl http://localhost:8000/files/image.png -o downloaded-image.png
```

**Compare checksums**
```text
shasum -a 256 image.png downloaded-image.png
```

**Expected**
when comparing a downloaded image from a bucket with its original, their checksums should be the same

**Output**
```text
INFO:   <client-ip>:<port> - "POST /files/image.png HTTP/1.1" 200 OK

# Upload image
{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"image.png","content_type":"image/png"}

# Download image
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   724  100   724    0     0  85026      0 --:--:-- --:--:-- --:--:-- 90500

# Compare checksums are the same
4e88b7c9bd15d915fd2793820df1aa61c10199f7e192ebd4a5f32b80dcbcb273  image.png
4e88b7c9bd15d915fd2793820df1aa61c10199f7e192ebd4a5f32b80dcbcb273  downloaded-image.png
```

#### Scenario 31: Overwrite an existing object and check GET returns new content
**Pre-conditions**
A bucket exists with an object (txt file)

**1. Update content with new data**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  -H "Content-Type: text/plain" \
  --data-binary 'New data added'
```

**Read object**
```text
curl "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket"
```

**Expected**
Only the new content is displayed

**Output**
```text
# Update object
INFO:  <client-ip>:<port> - "PUT /objects/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object written successfully"}

# Read object
INFO:  <client-ip>:<port> - "GET /objects/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK
New data added
```

#### Scenario 32: Get Object Size changes as data gets updated
**Pre-conditions**
A bucket exists with one object/file

**1. Get object size with basic data**
```text
curl "http://localhost:8000/objects/sample.txt/size?bucket_name=test-bucket"
```
**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/sample.txt/size?bucket_name=test-bucket HTTP/1.1" 200 OK
{"bucket_name":"test-bucket","object_key":"sample.txt","size":47}
```
**2. Update object content with less data**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  -H "Content-Type: text/plain" \
  --data-binary 'New data added'

curl "http://localhost:8000/objects/sample.txt/size?bucket_name=test-bucket"
```
**Output**
```text
INFO:  <client-ip>:<port> - "GET /objects/sample.txt/size?bucket_name=test-bucket HTTP/1.1" 200 OK
{"bucket_name":"test-bucket","object_key":"sample.txt","size":14}
```

**3. Update content with more data**
```text
curl -X PUT \
  "http://localhost:8000/objects/sample.txt?bucket_name=test-bucket" \
  -H "Content-Type: text/plain" \
  --data-binary 'Adding more data to be stored to the S3 bucket. Adding more data to be stored to the S3 bucket. Adding more data to be stored to the S3 bucket. Adding more data to be stored to the S3 bucket'

curl "http://localhost:8000/objects/sample.txt/size?bucket_name=test-bucket"
```

**Expected**
Data size changes according to the amount of updated data to the object

**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/sample.txt/size?bucket_name=test-bucket HTTP/1.1" 200 OK
{"bucket_name":"test-bucket","object_key":"sample.txt","size":190}
```

##### Scenario 33: Delete object then confirm removal

**1. Create Bucket**
```text
curl -X POST "http://localhost:8000/buckets?bucket_name=test-bucket"
```

**2. Upload object**
```text
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt
```

**3. Delete object**
```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**4. Read Object**
```text
curl "http://localhost:8000/objects/non-ascii-sample.txt?bucket_name=test-bucket"
```

**Expected**
Object reading failed since object in bucket has been already deleted

**Output**
```text
INFO:   <client-ip>:<port> - "GET /objects/non-ascii-sample.txt?bucket_name=test-bucket HTTP/1.1" 500 Internal Server Error

{"detail":"Object reading failed"}
```

#### Scenario 34: Create and upload a file to a bucket, then apply file/object related operations such as list, download, compare and delete file.

**1. Create a sample file**
```text
echo "Hello from local MinIO S3 automation framework" > sample.txt
```

**Expected**
File created

**2. Upload the file**
```text
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt
```

**Expected**
Object uploaded successfully

**Output**
```text
portfolio-storage-api  | INFO: - "POST /files/sample.txt HTTP/1.1" 200 OK

{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"sample.txt","content_type":"text/plain"}
```

**3. List files**
```text
curl "http://localhost:8000/files?bucket_name=test-bucket"
```

**Expected**
bucket object(s) listed

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","objects":[{"key":"sample.txt","size":47,"last_modified":"2026-05-13T03:35:45.022000+00:00"}]}
```

**4. Download the file**
```text
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt
```

**Expected**
File is downloaded successfully and its content matches the uploaded file

**Output**
```text
portfolio-storage-api  | INFO: - "GET /files/sample.txt HTTP/1.1" 200 OK

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    47  100    47    0     0   3523      0 --:--:-- --:--:-- --:--:--  3615
```

```text
cat downloaded-sample.txt:
Hello from local MinIO S3 automation framework
```

**5. Compare files**
```text
diff sample.txt downloaded-sample.txt
```

**Expected**
If there is no output from diff, the files match.

**6. Delete the file**
```text
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"
```

**Expected**
Object deleted successfully

**Output**
```text
portfolio-storage-api  | INFO: - "DELETE /files/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}
```
