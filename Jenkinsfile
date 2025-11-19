pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
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

        JIRA_URL            = credentials('jira-base-url')      // Your Jira base URL
        JIRA_USER           = credentials('jira-user')          // Username
        RTM_API_TOKEN       = credentials('rtm-api-key')        // RTM API Token
        RTM_BASE_URL        = credentials('rtm-base-url')       // RTM BASE URL
        PROJECT_KEY         = 'RTM-TEST'                        // JIRA PROJECT KEY
        REPORT_TYPE         = 'JUNIT'                           // JUNIT TESTING REPORT TYPE
        CI_JOB_URL          = "${env.BUILD_URL}"                // JENKINS BUILD URL
        TEST_RESULTS_DIR    = 'test-results'                    // TEST RESULTS
        TEST_RESULTS_ZIP    = 'test-results.zip'                // TEST RESULT ZIP FILE

        // ==============================
        // GitHub Login Credentials Setup
        // ===============================

        GITHUB_CREDENTIALS = credentials('github-credentials')

        // ============================
        // Reports Path Setup
        // ============================

        REPORT_PATH   = 'report/report.html'
        REPORT_DIR    = 'report'
        VERSION_FILE  = 'report/version.txt'

        // =================================
        // Python Virtual & Cache path Setup
        // =================================

        VENV_PATH       = "C:\\jenkins_work\\venv"
        PIP_CACHE_DIR   = "C:\\jenkins_home\\pip-cache"

        PYTHONUTF8                  = '1'
        PYTHONIOENCODING            = 'utf-8'
        PYTHONLEGACYWINDOWSSTDIO    = '1'
    }

    parameters {
        
        // =================================
        // RTM TEST Exection Parameter Setup
        // =================================
        string(name: 'RTM_TEST_EXECUTION_KEY', defaultValue: '', description: 'RTM Test Execution key')
        string(name: 'RTM_TEST_PLAN_KEY', defaultValue: '', description: 'RTM Test Plan key (optional)')
        string(name: 'RTM_TRIGGERED_BY', defaultValue: '', description: 'RTM user who triggered the run')
    }

    stages {

        // ============================
        // Setup Encoding Stage
        // ============================

        stage('Setup Encoding') {
            steps {
                echo 'Setting UTF-8 encoding...'
                bat """
                    @echo off
                    chcp 65001 >nul
                """
            }
        }

        // ============================
        // Checkout GitHub Stage
        // ============================

        stage('Checkout GitHub') {
            steps {
                echo 'Checking out source code...'

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/cicd-pipeline-automation/flask-login-app-rtm-automation.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])

                echo 'Checkout complete.'
            }
        }

        // ============================
        // Setup Python Stage
        // ============================

        stage('Setup Python') {
            steps {
                echo "Ensuring Python virtual environment exists..."

                // REUSE VENV → DO NOT DELETE ANYMORE
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
        // Install Dependencies Stage
        // ============================

        stage('Install Dependencies') {
            steps {
                echo 'Installing dependencies...'
                bat """
                    @echo off

                    if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"

                    rem === Install only when requirements changed ===
                    if exist requirements.lock (
                        fc requirements.txt requirements.lock >nul
                        if %errorlevel%==0 (
                            echo Requirements unchanged. Skipping pip install.
                            exit /b 0
                        )
                    )

                    echo Installing dependencies...
                    "%VENV_PATH%\\Scripts\\pip.exe" install ^
                        --prefer-binary ^
                        --cache-dir "%PIP_CACHE_DIR%" ^
                        -r requirements.txt

                    copy /Y requirements.txt requirements.lock >nul
                """
            }
        }

        // ================================
        // Run Tests & Generate JUnit Stage
        // =================================

        stage('Run Tests & Generate JUnit') {
            steps {
                echo "🧪 Running tests and generating JUnit XML..."
                bat """
                    if not exist ${TEST_RESULTS_DIR} mkdir ${TEST_RESULTS_DIR}
                    pytest --junitxml=${TEST_RESULTS_DIR}/junit-report.xml
                """
            }

            post {
                always {
                    junit allowEmptyResults: true, testResults: "${TEST_RESULTS_DIR}/junit-*.xml"
                }
            }
        }

        // ============================
        // Generate Test Report Stage
        // ============================

        stage('Generate Report') {
            steps {
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

        // ==================================
        // Publish Report to Confluence Stage
        // ==================================

        stage('Publish Report to Confluence') {
            steps {
                bat """
                    timeout /t 2 >nul
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/publish_report_confluence.py
                """
            }
        }

        // ============================
        // Email Report Stage
        // ============================

        stage('Email Report') {
            steps {
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/send_report_email.py
                """
            }
        }

        // =====================================
        // Archive Test Results Stage
        // =====================================

        stage('Archive Test Results') {
            steps {
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

        // =====================================
        // Upload Results to RTM Stage
        // =====================================

        stage('Upload Results to RTM') {
            when {
                expression { params.RTM_TEST_EXECUTION_KEY?.trim() }
            }
            steps {
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
            echo 'PIPELINE COMPLETED SUCCESSFULLY'
        }
        failure {
            echo 'PIPELINE FAILED — Check logs!'
        }
        always {
            echo 'Cleaning workspace complete.'
        }
    }
}
