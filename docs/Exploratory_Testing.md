# Exploratory Test Document:

## Purpose
Document to show the initial manual testing activity to understand and validate the product.

## Test Scenarios
### Scenario 1: Check FastAPI health:
curl http://localhost:8000/health

**Output**
portfolio-storage-api  | INFO:  "GET /health HTTP/1.1" 200 OK
{"status":"ok","service":"storage-api"}

### Scenario 2: Bootstrap the S3 bucket:
curl -X POST "http://localhost:8000/buckets/bootstrap?bucket_name=test-bucket"

**Output**
portfolio-storage-api  | INFO:  - "POST /buckets/bootstrap?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","status":"ready"}

### Scenario 3: Create and upload a file to a bucket, then apply file/object related opearations such as list, download, compare and delte file.

#### 3.1 Create a sample file:
echo "Hello from local MinIO S3 automation framework" > sample.txt

#### 3.2 Upload the file
curl -X POST \
  -F "file=@sample.txt" \
  http://localhost:8000/files/sample.txt

**Output**
portfolio-storage-api  | INFO: - "POST /files/sample.txt HTTP/1.1" 200 OK

{"message":"Object uploaded successfully","bucket":"test-bucket","object_key":"sample.txt","content_type":"text/plain"}

#### 3.3 List files:
curl "http://localhost:8000/files?bucket_name=test-bucket"

**Output**
portfolio-storage-api  | INFO: - "GET /files?bucket_name=test-bucket HTTP/1.1" 200 OK

{"bucket":"test-bucket","objects":[{"key":"sample.txt","size":47,"last_modified":"2026-05-13T03:35:45.022000+00:00"}]}

#### 3.4 Download the file:
curl http://localhost:8000/files/sample.txt -o downloaded-sample.txt

**Output**
portfolio-storage-api  | INFO: - "GET /files/sample.txt HTTP/1.1" 200 OK

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    47  100    47    0     0   3523      0 --:--:-- --:--:-- --:--:--  3615

cat downloaded-sample.txt:
Hello from local MinIO S3 automation framework

#### 3.5 Compare files:
diff sample.txt downloaded-sample.txt

**Note**: If there is no output from diff, the files match.

#### 3.6 Delete the file:
curl -X DELETE "http://localhost:8000/files/sample.txt?bucket_name=test-bucket"

**Output**
portfolio-storage-api  | INFO: - "DELETE /files/sample.txt?bucket_name=test-bucket HTTP/1.1" 200 OK

{"message":"Object deleted successfully","bucket_name":"test-bucket","object_key":"sample.txt"}

