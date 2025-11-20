/**************************************************************
 🏗️  JENKINS PIPELINE — FLASK LOGIN → RTM → JIRA → CONFLUENCE
**************************************************************/

pipeline {
    agent any

    /******************************************************
     🛠️ PIPELINE OPTIONS
    ******************************************************/
    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    /******************************************************
     🔐 ENVIRONMENT VARIABLES
    ******************************************************/
    environment {
        /* ===================== SMTP ====================== */
        SMTP_HOST       = credentials('smtp-host')
        SMTP_PORT       = '587'
        SMTP_USER       = credentials('smtp-user')
        SMTP_PASS       = credentials('smtp-pass')
        REPORT_FROM     = credentials('sender-email')
        REPORT_TO       = credentials('receiver-email')
        REPORT_CC       = credentials('cc-email')
        REPORT_BCC      = credentials('bcc-email')

        /* ================ Confluence Access =============== */
        CONFLUENCE_BASE  = credentials('confluence-base')
        CONFLUENCE_USER  = credentials('confluence-user')
        CONFLUENCE_TOKEN = credentials('confluence-token')
        CONFLUENCE_SPACE = "RTMTESTAUT"
        CONFLUENCE_TITLE = "Test Result Report"

        /* ================== Jira + RTM ==================== */
        JIRA_URL        = credentials('jira-base-url')
        JIRA_USER       = credentials('jira-user')
        JIRA_API_TOKEN  = credentials('jira-api-token')

        RTM_API_TOKEN   = credentials('rtm-api-key')
        RTM_BASE_URL    = credentials('rtm-base-url')
        PROJECT_KEY     = "RT"

        /* =================== GitHub ======================= */
        GITHUB_CREDENTIALS = credentials('github-credentials')

        /* ===================== Paths ====================== */
        REPORT_DIR        = 'report'
        TEST_RESULTS_DIR  = 'report'
        TEST_RESULTS_ZIP  = 'test-results.zip'

        VENV_PATH         = "C:\\jenkins_work\\venv"
        PIP_CACHE_DIR     = "C:\\jenkins_home\\pip-cache"

        /* ===================== Python UTF8 Setup ====================== */
        PYTHONUTF8 = '1'
        PYTHONLEGACYWINDOWSSTDIO = '1'

        /* ===================== Test Case Action ====================== */
        FORCE_FAIL = false
    }

    /******************************************************
     🚀 PIPELINE STAGES
    ******************************************************/
    stages {

        /**********************************************
         1️⃣ CHECKOUT SOURCE CODE
        **********************************************/
        stage('Checkout GitHub') {
            steps {
                echo "📦 Checking out source code..."
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

        /**********************************************
         2️⃣ PYTHON SETUP
        **********************************************/
        stage('Setup Python') {
            steps {
                echo "🐍 Preparing Python virtual environment..."
                bat """
                    @echo off
                    if not exist "%VENV_PATH%" (
                        python -m venv "%VENV_PATH%"
                    )
                    "%VENV_PATH%\\Scripts\\pip.exe" install --upgrade pip setuptools wheel ^
                        --cache-dir "%PIP_CACHE_DIR%"
                """
            }
        }

        /**********************************************
         3️⃣ INSTALL DEPENDENCIES
        **********************************************/
        stage('Install Dependencies') {
            steps {
                echo "📥 Installing Python dependencies..."
                bat """
                    "%VENV_PATH%\\Scripts\\pip.exe" install -r requirements.txt ^
                        --cache-dir "%PIP_CACHE_DIR%"
                """
            }
        }

        /**********************************************
         4️⃣ RUN TESTS
        **********************************************/
        stage('Run Tests & Generate JUnit') {
            steps {
                echo "🧪 Running tests..."
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

        /**********************************************
         5️⃣ GENERATE CUSTOM REPORT
        **********************************************/
        stage('Generate Report') {
            steps {
                echo "📝 Generating enhanced HTML/PDF report..."
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

        /**********************************************
         6️⃣ PUBLISH TO CONFLUENCE
        **********************************************/
        stage('Publish Report to Confluence') {
            steps {
                echo "🌐 Publishing report to Confluence..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/publish_report_confluence.py
                """
            }
        }

        /**********************************************
         7️⃣ ZIP TEST RESULTS
        **********************************************/
        stage('Archive Test Results') {
            steps {
                echo "📦 Packaging test results ZIP..."
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

        /**********************************************
         8️⃣ UPLOAD RESULTS TO RTM
        **********************************************/
        stage('Upload Results to RTM') {
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

        /**********************************************
         ⭐  NEW: CREATE JIRA TEST EXECUTION
        **********************************************/
        stage('Create Jira Test Execution') {
            steps {
                echo "📘 Creating Jira Test Execution Issue..."

                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/create_jira_execution.py ^
                        --project "%PROJECT_KEY%" ^
                        --summary "Automated Test Execution - Build ${BUILD_NUMBER}" ^
                        --output "rtm_jira_issue.txt"
                """

                script {
                    env.JIRA_EXEC_KEY = readFile("rtm_jira_issue.txt").trim()
                    echo "📘 Jira Execution Key: ${env.JIRA_EXEC_KEY}"
                }
            }
        }

        /**********************************************
         9️⃣ ATTACH PDF/HTML TO JIRA
        **********************************************/
        stage('Attach Reports to RTM') {
            steps {
                echo "📚 Attaching reports to Jira Test Execution..."

                script {
                    def version = readFile("report/version.txt").trim()
                    echo "ℹ Version: v${version}"

                    def issueKey = readFile("rtm_jira_issue.txt").trim()
                    echo "ℹ Jira Test Execution: ${issueKey}"

                    def pdfFile  = "report/test_result_report_v${version}.pdf"
                    def htmlFile = "report/test_result_report_v${version}.html"

                    echo "📄 PDF: ${pdfFile}"
                    echo "🌐 HTML: ${htmlFile}"

                    def status = bat(
                        returnStatus: true,
                        script: """
                            "%VENV_PATH%\\Scripts\\python.exe" scripts\\rtm_attach_reports.py ^
                                --issueKey "${issueKey}" ^
                                --pdf "${pdfFile}" ^
                                --html "${htmlFile}"
                        """
                    )

                    if (status != 0) {
                        error("❌ Jira Attachment Failed — stopping pipeline")
                    } else {
                        echo "✅ Attachments uploaded successfully!"
                    }
                }
            }
        }

        /**********************************************
         🔟 EMAIL REPORT
        **********************************************/
        stage('Email Report') {
            steps {
                echo "📧 Sending email report..."
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts/send_report_email.py
                """
            }
        }
    }

    /******************************************************
     🧹 FINAL ACTIONS
    ******************************************************/
    post {
        success {
            echo "🎉 PIPELINE COMPLETED SUCCESSFULLY"
        }
        failure {
            echo "❌ PIPELINE FAILED — Check logs!"
        }
        always {
            echo "🧹 Cleaning workspace complete."
        }
    }
}
