/**************************************************************
 🏗️  JENKINS PIPELINE — FLASK LOGIN → RTM → JIRA → CONFLUENCE
 📌 Purpose:
     - Run automated tests
     - Generate HTML/PDF reports
     - Publish reports to Confluence
     - Email results to stakeholders
     - Upload JUnit results to RTM
     - Attach PDF/HTML reports to RTM via Jira API
**************************************************************/

pipeline {
    agent any

    /******************************************************
     🛠️ PIPELINE OPTIONS
    ******************************************************/
    options {
        timestamps()                     // Show timestamps in logs
        disableConcurrentBuilds()        // Avoid parallel overlapping runs
        skipDefaultCheckout()            // We manually checkout using GitSCM
        buildDiscarder(logRotator(numToKeepStr: '20')) // Keep last 20 builds
    }

    /******************************************************
     🔐 SECURE ENVIRONMENT VARIABLES (Credentials + Paths)
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

        PYTHONUTF8             = '1'
        PYTHONLEGACYWINDOWSSTDIO = '1'

        /* ===================== Test Case Action ====================== */
        FORCE_FAIL = false
    }

    // /******************************************************
    //  📝 USER PARAMETERS
    // ******************************************************/
    // parameters {
    //     string(name: 'RTM_TRIGGERED_BY', defaultValue: 'devopsuser8413', description: 'RTM user who requested this execution')
    // }

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
         2️⃣ PYTHON SETUP (Persistent Virtualenv)
        **********************************************/
        stage('Setup Python') {
            steps {
                echo "🐍 Preparing Python virtual environment..."
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

        /**********************************************
         3️⃣ INSTALL PYTHON DEPENDENCIES
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
         4️⃣ RUN TESTS & GENERATE JUNIT XML
        **********************************************/
        stage('Run Tests & Generate JUnit') {
            steps {
                echo "🧪 Running tests + generating JUnit report..."
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
         5️⃣ GENERATE CUSTOM HTML+PDF REPORT
        **********************************************/
        stage('Generate Report') {
            steps {
                echo "📝 Building enhanced HTML/PDF report..."
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
         6️⃣ PUBLISH REPORT TO CONFLUENCE
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
         7️⃣ ARCHIVE TEST RESULTS
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
         8️⃣ UPLOAD RESULTS TO RTM (JUnit ZIP)
        **********************************************/
        stage('Upload Results to RTM') {
            steps {
                echo "📤 Uploading results to RTM..."
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
         9️⃣ ATTACH PDF/HTML REPORTS TO RTM (via Jira)
        **********************************************/
        stage('Attach Reports to RTM') {
            steps {
                echo "📚 Attaching HTML/PDF reports to RTM..."

                script {
                    // Read version OUTSIDE of bat step, stored in Jenkins binding
                    version = readFile("report/version.txt").trim()
                    echo "ℹ Using report version: v${version}"

                    pdfFile = "report/test_result_report_v${version}.pdf"
                    htmlFile = "report/test_result_report_v${version}.html"

                    echo "📄 PDF: ${pdfFile}"
                    echo "🌐 HTML: ${htmlFile}"
                }

                // Use version (from outer scope) inside bat
                bat """
                    "%VENV_PATH%\\Scripts\\python.exe" scripts\\rtm_attach_reports.py ^
                    --pdf "report/test_result_report_v${version}.pdf" ^
                    --html "report/test_result_report_v${version}.html"
                """
            }
        }

        /**********************************************
         🔟 EMAIL REPORT TO STAKEHOLDERS
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
     🧹 POST-PIPELINE ACTIONS
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
