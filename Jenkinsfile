pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout()   // prevents duplicate initial SCM checkout
    }

    environment {

        // =============================
        // SMTP Login Credentials Setup
        // =============================
        SMTP_HOST        = credentials('smtp-host')
        SMTP_PORT        = '587'
        SMTP_USER        = credentials('smtp-user')
        SMTP_PASS        = credentials('smtp-pass')
        REPORT_FROM      = credentials('sender-email')
        REPORT_TO        = credentials('receiver-email')
        REPORT_CC        = credentials('cc-email')
        REPORT_BCC       = credentials('bcc-email')

        // ==================================
        // Confluence Login Credentials Setup
        // ==================================
        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = 'DEMO'
        CONFLUENCE_TITLE = 'Test Result Report'

        // ==================================
        // JIRA & RTM Login Credentials Setup
        // ==================================
        JIRA_URL          = credentials('jira-base-url')
        JIRA_USER         = credentials('jira-user')
        RTM_API_TOKEN     = credentials('rtm-api-key')
        RTM_BASE_URL      = credentials('rtm-base-url')
        PROJECT_KEY       = 'RTM-TEST'
        REPORT_TYPE       = 'JUNIT'
        CI_JOB_URL        = "${env.BUILD_URL}"
        TEST_RESULTS_DIR  = 'test-results'
        TEST_RESULTS_ZIP  = 'test-results.zip'

        // ============================
        // GitHub Login Credential
        // ============================
        GITHUB_CREDENTIALS = credentials('github-credentials')

        // ============================
        // Reports Path Setup
        // ============================
        REPORT_DIR    = 'report'
        VERSION_FILE  = 'report/version.txt'
        REPORT_PATH   = 'report/report.html'

        // =================================
        // Python Virtual & Cache path Setup
        // =================================
        VENV_PATH     = "C:\\jenkins_work\\venv"
        PIP_CACHE_DIR = "C:\\jenkins_home\\pip-cache"

        PYTHONUTF8                  = '1'
        PYTHONIOENCODING            = 'utf-8'
        PYTHONLEGACYWINDOWSSTDIO    = '1'

        // =================================
        // Python Testing Failure Action
        // =================================
        FORCE_FAIL = "false"
    }

    parameters {
        string(name: 'RTM_TEST_EXECUTION_KEY', defaultValue: 'RT-55', description: 'RTM Test Execution key')
        string(name: 'RTM_TEST_PLAN_KEY', defaultValue: 'RT-54', description: 'RTM Test Plan key (optional)')
        string(name: 'RTM_TRIGGERED_BY', defaultValue: 'devopsuser8413', description: 'RTM user who triggered the run')
    }

    stages {

        // ============================
        // Checkout Source Code
        // ============================
        stage('Checkout GitHub') {
            steps {
                echo '📦 Checking out source code...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/cicd-pipeline-automation/flask-login-app-rtm-automation.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])
            }
        }

        // ============================
        // Setup Python (Persistent venv)
        // ============================
        stage('Setup Python') {
            steps {
                echo "📌 Preparing Python virtual environment..."
                bat """
                    @echo off
                    if not exist "%VENV_PATH%" (
                        echo Creating new venv...
                        python -m venv "%VENV_PATH%"
                    )

                    "%VENV_PATH%\\Scripts\\python.exe" -m pip install --upgrade pip setuptools wheel ^
                        --cache-dir "%PIP_CACHE_DIR%"
                """
            }
        }

        // ============================
        // Install Dependencies
        // ============================
        stage('Install Dependencies') {
            steps {
                echo "📥 Installing Python dependencies..."
                bat """
                    @echo off
                    if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"

                    if exist requirements.lock (
                        fc requirements.txt requirements.lock >nul
                        if %errorlevel%==0 (
                            echo 🔄 Requirements unchanged. Skipping installation.
                            exit /b 0
                        )
                    )

                    echo 📦 Installing Python packages...
                    "%VENV_PATH%\\Scripts\\pip.exe" install ^
                        --prefer-binary ^
                        --cache-dir "%PIP_CACHE_DIR%" ^
                        -r requirements.txt || exit /b 1

                    copy /Y requirements.txt requirements.lock >nul
                """
            }
        }

        // ============================
        // Run Tests + JUnit XML
        // ============================
        stage('Run Tests & Generate JUnit') {
            steps {
                echo "🧪 Running tests + generating JUnit XML..."
                bat """
                    pip install pytest-html
                    if not exist report mkdir report

                    "%VENV_PATH%\\Scripts\\pytest.exe" ^
                        --junitxml=report/junit.xml ^
                        --log-file=report/pytest_output.txt ^
                        --log-file-level=INFO ^
                        --html=report/report.html ^
                        --self-contained-html
                """
            }
        }

        // ============================
        // Generate HTML/PDF Report
        // ============================
        stage('Generate Report') {
            steps {
                echo "📝 Generating enhanced HTML/PDF report..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/generate_report.py
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/test_result_report_v*.html', fingerprint: true
                    archiveArtifacts artifacts: 'report/test_result_report_v*.pdf', fingerprint: true
                    archiveArtifacts artifacts: 'report/version.txt', fingerprint: true
                }
            }
        }

        // ============================
        // Publish to Confluence
        // ============================
        stage('Publish Report to Confluence') {
            steps {
                echo "🌐 Publishing report to Confluence..."
                bat """
                    timeout /t 2 >nul
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/publish_report_confluence.py
                """
            }
        }

        // ============================
        // Email Report
        // ============================
        stage('Email Report') {
            steps {
                echo "📧 Sending email report..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/send_report_email.py
                """
            }
        }

        // ============================
        // Archive Test Results ZIP
        // ============================
        stage('Archive Test Results') {
            steps {
                echo "📦 Packaging test results..."
                powershell """
                    if (Test-Path ${env.TEST_RESULTS_ZIP}) { Remove-Item ${env.TEST_RESULTS_ZIP} }
                    Add-Type -AssemblyName System.IO.Compression.FileSystem
                    [IO.Compression.ZipFile]::CreateFromDirectory('${env.TEST_RESULTS_DIR}', '${env.TEST_RESULTS_ZIP}')
                """
            }
            post {
                success {
                    archiveArtifacts artifacts: "${TEST_RESULTS_ZIP}", fingerprint: true
                }
            }
        }

        // ============================
        // Upload to RTM
        // ============================
        stage('Upload Results to RTM') {
            when {
                expression { params.RTM_TEST_EXECUTION_KEY?.trim() }
            }
            steps {
                echo "📤 Uploading results to RTM..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/rtm_upload_results.py ^
                        --archive "${TEST_RESULTS_ZIP}" ^
                        --test-exec "${params.RTM_TEST_EXECUTION_KEY}" ^
                        --rtm-base "${RTM_BASE_URL}" ^
                        --project "${PROJECT_KEY}"
                """
            }
        }
    }

    post {
        success {
            echo '🎉 PIPELINE COMPLETED SUCCESSFULLY'
        }
        failure {
            echo '❌ PIPELINE FAILED — Check logs!'
        }
        always {
            echo '🧹 Cleaning workspace complete.'
        }
    }
}
