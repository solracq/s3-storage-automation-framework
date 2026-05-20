pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        BASE_PATH = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
        VENV_DIR = '.venv'
        REPORT_DIR = 'reports'
        JUNIT_DIR = 'reports/junit'
        PYTEST_LOG_ROOT = 'reports/logs'
        COMPOSE_PROJECT_NAME = "s3-ci-${BUILD_NUMBER}"
        MINIO_API_HOST_PORT = '19000'
        MINIO_CONSOLE_HOST_PORT = '19001'
        STORAGE_API_HOST_PORT = '18000'
    }

    stages {
        stage('Build') {
            steps {
                sh '''
                    set -eu
                    export PATH="${BASE_PATH}:$PATH"

                    mkdir -p "${REPORT_DIR}" "${JUNIT_DIR}" "${PYTEST_LOG_ROOT}" "${REPORT_DIR}/artifacts"

                    minio_user="${MINIO_ROOT_USER:-minioadmin}"
                    minio_password="${MINIO_ROOT_PASSWORD:-minioadmin123}"
                    aws_key="${AWS_ACCESS_KEY_ID:-$minio_user}"
                    aws_secret="${AWS_SECRET_ACCESS_KEY:-$minio_password}"
                    aws_region="${AWS_REGION:-us-east-1}"
                    bucket_name="${MINIO_BUCKET_NAME:-test-bucket}"
                    public_s3_endpoint="${S3_PUBLIC_ENDPOINT_URL:-http://127.0.0.1:${MINIO_API_HOST_PORT}}"
                    internal_s3_endpoint="${S3_ENDPOINT_URL:-http://minio:9000}"

                    cat > .env <<EOF
MINIO_ROOT_USER=${minio_user}
MINIO_ROOT_PASSWORD=${minio_password}
AWS_ACCESS_KEY_ID=${aws_key}
AWS_SECRET_ACCESS_KEY=${aws_secret}
AWS_REGION=${aws_region}
MINIO_BUCKET_NAME=${bucket_name}
S3_ENDPOINT_URL=${internal_s3_endpoint}
S3_PUBLIC_ENDPOINT_URL=${public_s3_endpoint}
MINIO_API_HOST_PORT=${MINIO_API_HOST_PORT}
MINIO_CONSOLE_HOST_PORT=${MINIO_CONSOLE_HOST_PORT}
STORAGE_API_HOST_PORT=${STORAGE_API_HOST_PORT}
EOF

                    python3 -m venv "${VENV_DIR}"
                    "${VENV_DIR}/bin/python" -m pip install --upgrade pip
                    "${VENV_DIR}/bin/pip" install -r requirements.txt

                    docker compose config >/dev/null
                    docker compose build storage-api
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    sh '''
                        set -eu
                        export PATH="${BASE_PATH}:$PATH"

                        mkdir -p "${PYTEST_LOG_ROOT}/unit"

                        PYTEST_LOG_DIR="${PYTEST_LOG_ROOT}/unit" \
                        PYTEST_LOG_FILE="unit.log" \
                        PYTEST_CONSOLE_LOG_LEVEL=INFO \
                        "${VENV_DIR}/bin/python" -m pytest tests/unit -q \
                          --junitxml="${JUNIT_DIR}/unit.xml"
                    '''
                }
            }
        }

        stage('Smoke Tests') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    sh '''
                        set -eu
                        export PATH="${BASE_PATH}:$PATH"

                        mkdir -p "${PYTEST_LOG_ROOT}/smoke"

                        docker compose down -v --remove-orphans || true
                        docker compose up -d minio

                        for attempt in $(seq 1 30); do
                            if curl -fsS "http://127.0.0.1:${MINIO_API_HOST_PORT}/minio/health/live" >/dev/null; then
                                break
                            fi
                            sleep 2
                        done

                        curl -fsS "http://127.0.0.1:${MINIO_API_HOST_PORT}/minio/health/live" >/dev/null

                        PYTEST_LOG_DIR="${PYTEST_LOG_ROOT}/smoke" \
                        PYTEST_LOG_FILE="smoke.log" \
                        PYTEST_CONSOLE_LOG_LEVEL=INFO \
                        S3_PUBLIC_ENDPOINT_URL="http://127.0.0.1:${MINIO_API_HOST_PORT}" \
                        "${VENV_DIR}/bin/python" -m pytest -v -s -m smoke \
                          --junitxml="${JUNIT_DIR}/smoke.xml"
                    '''
                }
            }
        }

        stage('Regression Tests') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    sh '''
                        set -eu
                        export PATH="${BASE_PATH}:$PATH"

                        mkdir -p "${PYTEST_LOG_ROOT}/regression"

                        docker compose down -v --remove-orphans || true
                        docker compose up -d minio

                        for attempt in $(seq 1 30); do
                            if curl -fsS "http://127.0.0.1:${MINIO_API_HOST_PORT}/minio/health/live" >/dev/null; then
                                break
                            fi
                            sleep 2
                        done

                        curl -fsS "http://127.0.0.1:${MINIO_API_HOST_PORT}/minio/health/live" >/dev/null

                        # Regression currently runs the broader non-unit suite after smoke,
                        # excluding the dedicated smoke stage to avoid duplicate execution.
                        PYTEST_LOG_DIR="${PYTEST_LOG_ROOT}/regression" \
                        PYTEST_LOG_FILE="regression.log" \
                        PYTEST_CONSOLE_LOG_LEVEL=INFO \
                        S3_PUBLIC_ENDPOINT_URL="http://127.0.0.1:${MINIO_API_HOST_PORT}" \
                        "${VENV_DIR}/bin/python" -m pytest -v -s -m "not unit and not smoke" \
                          --junitxml="${JUNIT_DIR}/regression.xml"
                    '''
                }
            }
        }

        stage('Test Report Publication') {
            steps {
                sh '''
                    set +e
                    export PATH="${BASE_PATH}:$PATH"

                    mkdir -p "${REPORT_DIR}/artifacts"
                    docker compose ps > "${REPORT_DIR}/artifacts/docker-compose-ps.txt" 2>&1 || true
                    docker compose logs --no-color minio > "${REPORT_DIR}/artifacts/minio.log" 2>&1 || true
                '''

                junit allowEmptyResults: true, testResults: "${JUNIT_DIR}/*.xml"
                archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*'
            }
        }
    }

    post {
        always {
            sh '''
                set +e
                export PATH="${BASE_PATH}:$PATH"
                docker compose down -v --remove-orphans
            '''
        }
    }
}
