/**************************************************************
 🏗️  JENKINS PIPELINE — FLASK LOGIN → RTM → JIRA → CONFLUENCE
 📌 Purpose:
     • Execute automated tests
     • Generate HTML + PDF test reports
     • Upload test results to RTM
     • Attach formatted reports to Jira Test Execution
     • Publish reports to Confluence
     • Notify stakeholders via email
**************************************************************/

pipeline {
    agent any

    /**********************************************************
     ⚙ PIPELINE OPTIONS
    **********************************************************/
    options {
        timestamps()                     // Accurate timed logs
        disableConcurrentBuilds()        // No overlapping runs
        skipDefaultCheckout()            // Manual SCM checkout
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    /**********************************************************
     🔐 GLOBAL ENVIRONMENT VARIABLES
    **********************************************************/
    environment {

        /* ------------------ SMTP Email ------------------ */
        SMTP_HOST       = credentials('smtp-host')
        SMTP_PORT       = '587'
        SMTP_USER       = credentials('smtp-user')
        SMTP_PASS       = credentials('smtp-pass')
        REPORT_FROM     = credentials('sender-email')
        REPORT_TO       = credentials('receiver-email')
        REPORT_CC       = credentials('cc-email')
        REPORT_BCC      = credentials('bcc-email')

        /* ---------------- Confluence Access -------------- */
        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = "RTMTESTAUT"
        CONFLUENCE_TITLE = "Test Result Report"

        /* ------------------- Jira + RTM ------------------- */
        JIRA_URL        = credentials('jira-base-url')
        JIRA_USER       = credentials('jira-user')
        JIRA_API_TOKEN  = credentials('jira-api-token')

        RTM_API_TOKEN   = credentials('rtm-api-key')
        RTM_BASE_URL    = credentials('rtm-base-url')
        PROJECT_KEY     = "RT"

        /* ---------------- GitHub Checkout ---------------- */
        GITHUB_CREDENTIALS = credentials('github-credentials')

        /* ---------------- Reporting Paths ---------------- */
        REPORT_DIR        = 'report'
        TEST_RESULTS_DIR  = 'report'
        TEST_RESULTS_ZIP  = 'test-results.zip'

        /* ⚠ Placeholder — dynamically overwritten later */
        PDF_REPORT_PATH   = ""

        /* ---------------- Python Configuration ----------- */
        VENV_PATH         = "C:\\jenkins_work\\venv"
        PIP_CACHE_DIR     = "C:\\jenkins_home\\pip-cache"
        PYTHONUTF8        = '1'
        PYTHONLEGACYWINDOWSSTDIO = '1'

        FORCE_FAIL = false
    }

    /**********************************************************
     🧑‍🔧 USER PARAMETERS
    **********************************************************/
    parameters {
        string(
            name: 'RTM_TRIGGERED_BY',
            defaultValue: 'devopsuser8413',
            description: 'RTM user who initiated this execution'
        )
    }

    /**********************************************************
     🚀 PIPELINE STAGES
    **********************************************************/
    stages {

        /* ==================================================
         1) CHECKOUT SOURCE CODE
        ================================================== */
        stage('Checkout Source Code') {
            steps {
                echo "📦 Checking out source repository..."
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/old-code-fix']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/cicd-pipeline-automation/flask-login-app-rtm-automation.git',
                        credentialsId: 'github-credentials'
                    ]]
                ])
            }
        }

        /* ==================================================
         2) PREPARE PYTHON ENVIRONMENT
        ================================================== */
        stage('Setup Python Environment') {
            steps {
                echo "🐍 Setting up Python virtual environment..."
                bat """
                    @echo off
                    if not exist "%VENV_PATH%" (
                        echo Creating virtual environment...
                        python -m venv "%VENV_PATH%"
                    )
                    "%VENV_PATH%\\Scripts\\pip.exe" install --upgrade pip setuptools wheel ^
                        --cache-dir "%PIP_CACHE_DIR%"
                """
            }
        }

        /* ==================================================
         3) INSTALL PYTHON REQUIREMENTS
        ================================================== */
        stage('Install Python Dependencies') {
            steps {
                echo "📥 Installing required Python modules..."
                bat """
                    "%VENV_PATH%\\Scripts\\pip.exe" install -r requirements.txt ^
                        --cache-dir "%PIP_CACHE_DIR%"
                """
            }
        }

        /* ==================================================
         4) RUN TESTS + PRODUCE JUNIT XML
        ================================================== */
        stage('Run Tests & Generate JUnit Report') {
            steps {
                echo "🧪 Executing test suite..."
                bat """
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

        /* ==================================================
         5) GENERATE CUSTOM HTML + PDF REPORTS
        ================================================== */
        stage('Generate Final Test Report') {
            steps {
                echo "📝 Generating enhanced HTML/PDF reports..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/generate_report.py
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'report/test_result_report_v*.html'
                    archiveArtifacts artifacts: 'report/test_result_report_v*.pdf'
                    archiveArtifacts artifacts: 'report/version.txt'
                }
            }
        }

        /* ==================================================
         6) PUBLISH REPORT TO CONFLUENCE
        ================================================== */
        stage('Publish Report to Confluence') {
            steps {
                echo "🌐 Publishing report to Confluence..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/publish_report_confluence.py
                """
            }
        }

        /* ==================================================
         7) ATTACH HTML/PDF REPORTS → JIRA TEST EXECUTION
        ================================================== */
        stage('Attach Reports to RTM/Jira') {
            steps {
                echo "📚 Attaching PDF/HTML to Jira Test Execution..."

                script {
                    version = readFile("report/version.txt").trim()
                    echo "ℹ Detected report version: v${version}"

                    /* 🔥 Export version for all later stages */
                    env.REPORT_VERSION = version

                    /* 🔥 Build final PDF path & export globally */
                    env.PDF_REPORT_PATH = "report/test_result_report_v${version}.pdf"

                    echo "📄 PDF Path  : ${env.PDF_REPORT_PATH}"
                    echo "🌐 HTML Path : report/test_result_report_v${version}.html"
                }

                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts\\rtm_attach_reports.py ^
                    --pdf  "report/test_result_report_v${version}.pdf" ^
                    --html "report/test_result_report_v${version}.html"
                """
            }
        }

        /* ==================================================
         8) EMAIL REPORT TO STAKEHOLDERS
        ================================================== */
        stage('Email Report') {
            steps {
                echo "📧 Sending email notification..."
                echo "Using PDF_REPORT_PATH = ${env.PDF_REPORT_PATH}"
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/send_report_email.py
                """
            }
        }

        /* ==================================================
         9) PACKAGE TEST RESULTS ZIP
        ================================================== */
        stage('Archive Test Results') {
            steps {
                echo "📦 Creating ZIP archive of test results..."
                powershell """
                    if (Test-Path ${env.TEST_RESULTS_ZIP}) { Remove-Item ${env.TEST_RESULTS_ZIP} }
                    Add-Type -AssemblyName System.IO.Compression.FileSystem
                    [IO.Compression.ZipFile]::CreateFromDirectory('${env.TEST_RESULTS_DIR}', '${env.TEST_RESULTS_ZIP}')
                """
            }
            post {
                success {
                    archiveArtifacts artifacts: "${TEST_RESULTS_ZIP}"
                }
            }
        }

        /* ==================================================
         🔟 UPLOAD TEST RESULTS TO RTM
        ================================================== */
        stage('Upload JUnit ZIP to RTM') {
            steps {
                echo "📤 Uploading JUnit ZIP to RTM..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts\\rtm_upload_results.py ^
                    --archive "test-results.zip" ^
                    --rtm-base "%RTM_BASE_URL%" ^
                    --project "%PROJECT_KEY%" ^
                    --job-url "%BUILD_URL%"
                """
            }
        }
    }

    /**********************************************************
     🧹 POST-BUILD ACTIONS
    **********************************************************/
    post {
        success { echo "🎉 Pipeline completed successfully." }
        failure { echo "❌ Pipeline failed — please check logs." }
        always  { echo "🧹 Workspace cleanup completed." }
    }
}
