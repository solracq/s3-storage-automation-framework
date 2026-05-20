pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'SEND_EMAIL_NOTIFICATIONS',
            defaultValue: false,
            description: 'Send post-build emails through the email-ext plugin.'
        )
        string(
            name: 'EMAIL_RECIPIENTS',
            defaultValue: '',
            description: 'Optional comma-separated email recipients for build notifications.'
        )
    }

    // Set job behavior
    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    // Shared environment values
    environment {
        BASE_PATH = '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
        VENV_DIR = '.venv'
        REPORT_DIR = 'reports'
        JUNIT_DIR = 'reports/junit'
        REPORT_HTML_DIR = 'reports/html'
        PYTEST_LOG_ROOT = 'reports/logs'
        COMPOSE_PROJECT_NAME = "s3-ci-${BUILD_NUMBER}" // Isolates Docker resources by build number 
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

                    mkdir -p "${REPORT_DIR}" "${JUNIT_DIR}" "${REPORT_HTML_DIR}" "${PYTEST_LOG_ROOT}" "${REPORT_DIR}/artifacts"

                    # Build a CI-specific .env
                    minio_user="${MINIO_ROOT_USER:-minioadmin}"
                    minio_password="${MINIO_ROOT_PASSWORD:-minioadmin123}"
                    aws_key="${AWS_ACCESS_KEY_ID:-$minio_user}"
                    aws_secret="${AWS_SECRET_ACCESS_KEY:-$minio_password}"
                    aws_region="${AWS_REGION:-us-east-1}"
                    bucket_name="${MINIO_BUCKET_NAME:-test-bucket}"
                    public_s3_endpoint="${S3_PUBLIC_ENDPOINT_URL:-http://127.0.0.1:${MINIO_API_HOST_PORT}}"
                    internal_s3_endpoint="${S3_ENDPOINT_URL:-http://minio:9000}"

                    # Write the generated environment file
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
                    # Install Python dependencies
                    python3 -m venv "${VENV_DIR}"
                    "${VENV_DIR}/bin/python" -m pip install --upgrade pip
                    "${VENV_DIR}/bin/pip" install -r requirements.txt

                    # Validate Compose config
                    docker compose config >/dev/null

                    # Build the storage-api Docker image
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

                        # Teardown existing services
                        docker compose down -v --remove-orphans || true
                        # Start a fresh MinIO stack
                        docker compose up -d minio

                        # Wait for the health endpoint before running smoke tests
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

                    mkdir -p "${REPORT_DIR}/artifacts" "${REPORT_HTML_DIR}"
                    docker compose ps > "${REPORT_DIR}/artifacts/docker-compose-ps.txt" 2>&1 || true
                    docker compose logs --no-color minio > "${REPORT_DIR}/artifacts/minio.log" 2>&1 || true
                '''

                sh '''
                    set -eu
                    export PATH="${BASE_PATH}:$PATH"

                    "${VENV_DIR}/bin/python" scripts/generate_jenkins_test_report.py \
                      --input-dir "${JUNIT_DIR}" \
                      --html-dir "${REPORT_HTML_DIR}" \
                      --artifact-dir "${REPORT_DIR}/artifacts" \
                      --job-name "${JOB_NAME:-}" \
                      --build-number "${BUILD_NUMBER:-}" \
                      --build-url "${BUILD_URL:-}"
                '''

                junit allowEmptyResults: true, keepLongStdio: true, testResults: "${JUNIT_DIR}/*.xml"
                publishHTML(target: [
                    allowMissing: true,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: "${REPORT_HTML_DIR}",
                    reportFiles: 'index.html',
                    reportName: 'S3_Test_Summary'
                ])
                script {
                    def summary = new groovy.json.JsonSlurperClassic().parseText(
                        readFile("${REPORT_DIR}/artifacts/test-summary.json")
                    )
                    currentBuild.description = "Pass ${summary.total.passed} | Fail ${summary.total.failed} | Skip ${summary.total.skipped}"
                }
                archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*'
            }
        }
    }

    post {
        success {
            script {
                if (params.SEND_EMAIL_NOTIFICATIONS && params.EMAIL_RECIPIENTS?.trim()) {
                    def summaryText = fileExists("${REPORT_DIR}/artifacts/test-summary.txt")
                        ? readFile("${REPORT_DIR}/artifacts/test-summary.txt").trim()
                        : 'Test summary was not generated.'
                    try {
                        emailext(
                            to: params.EMAIL_RECIPIENTS.trim(),
                            subject: "[SUCCESS] ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                            mimeType: 'text/html',
                            body: """
                                <p><strong>Build result:</strong> SUCCESS</p>
                                <pre>${summaryText}</pre>
                                <p><a href="${env.BUILD_URL}testReport/">JUnit Test Report</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/html/index.html">HTML Test Summary</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/">Build Artifacts</a></p>
                            """
                        )
                    } catch (err) {
                        echo "Email notification failed: ${err.message}"
                    }
                } else {
                    echo 'Email notifications skipped: SEND_EMAIL_NOTIFICATIONS is false or EMAIL_RECIPIENTS is empty.'
                }
            }
        }
        unstable {
            script {
                if (params.SEND_EMAIL_NOTIFICATIONS && params.EMAIL_RECIPIENTS?.trim()) {
                    def summaryText = fileExists("${REPORT_DIR}/artifacts/test-summary.txt")
                        ? readFile("${REPORT_DIR}/artifacts/test-summary.txt").trim()
                        : 'Test summary was not generated.'
                    try {
                        emailext(
                            to: params.EMAIL_RECIPIENTS.trim(),
                            subject: "[UNSTABLE] ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                            mimeType: 'text/html',
                            body: """
                                <p><strong>Build result:</strong> UNSTABLE</p>
                                <pre>${summaryText}</pre>
                                <p><a href="${env.BUILD_URL}testReport/">JUnit Test Report</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/html/index.html">HTML Test Summary</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/">Build Artifacts</a></p>
                            """
                        )
                    } catch (err) {
                        echo "Email notification failed: ${err.message}"
                    }
                } else {
                    echo 'Email notifications skipped: SEND_EMAIL_NOTIFICATIONS is false or EMAIL_RECIPIENTS is empty.'
                }
            }
        }
        failure {
            script {
                if (params.SEND_EMAIL_NOTIFICATIONS && params.EMAIL_RECIPIENTS?.trim()) {
                    def summaryText = fileExists("${REPORT_DIR}/artifacts/test-summary.txt")
                        ? readFile("${REPORT_DIR}/artifacts/test-summary.txt").trim()
                        : 'Test summary was not generated.'
                    try {
                        emailext(
                            to: params.EMAIL_RECIPIENTS.trim(),
                            subject: "[FAILURE] ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                            mimeType: 'text/html',
                            body: """
                                <p><strong>Build result:</strong> FAILURE</p>
                                <pre>${summaryText}</pre>
                                <p><a href="${env.BUILD_URL}testReport/">JUnit Test Report</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/html/index.html">HTML Test Summary</a></p>
                                <p><a href="${env.BUILD_URL}artifact/reports/">Build Artifacts</a></p>
                            """
                        )
                    } catch (err) {
                        echo "Email notification failed: ${err.message}"
                    }
                } else {
                    echo 'Email notifications skipped: SEND_EMAIL_NOTIFICATIONS is false or EMAIL_RECIPIENTS is empty.'
                }
            }
        }
        always {
            sh '''
                set +e
                export PATH="${BASE_PATH}:$PATH"
                # Run even if tests fail. This keeps the local Jenkins box clean between runs.
                docker compose down -v --remove-orphans
            '''
        }
    }
}
