# Updated send_report_email.py with Jira Link Support
# (Full rewritten script based on user request)

import os
import sys
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

# =============================================================
# Environment Variables
# =============================================================
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

TO_RAW  = os.getenv('REPORT_TO', '')
CC_RAW  = os.getenv('REPORT_CC', '')
BCC_RAW = os.getenv('REPORT_BCC', '')
FROM_EMAIL = os.getenv('REPORT_FROM')

CONFLUENCE_PAGE_URL_ENV = os.getenv("CONFLUENCE_PAGE_URL", "")
JIRA_ISSUE_URL_ENV      = os.getenv("JIRA_ISSUE_URL", "")
CONF_LINK_FILE = "report/confluence_url.txt"

# =============================================================
# Helper Functions
# =============================================================
def read_confluence_url():
    """Reads the Confluence URL either from file or env"""
    if os.path.exists(CONF_LINK_FILE):
        return open(CONF_LINK_FILE).read().strip()
    return CONFLUENCE_PAGE_URL_ENV or ""


def read_jira_issue_url():
    """Reads Jira Test Execution Key and builds full URL"""
    # If explicit URL exists, use it
    if JIRA_ISSUE_URL_ENV:
        return JIRA_ISSUE_URL_ENV

    # Otherwise, read execution key from file
    if os.path.exists("rtm_execution_key.txt"):
        key = open("rtm_execution_key.txt").read().strip()
        jira_base = os.getenv("JIRA_URL", "").rstrip("/")
        if jira_base:
            return f"{jira_base}/browse/{key}"

    return ""


def clean_list(raw):
    return [e.strip() for e in raw.split(",") if e.strip()]


def send_single_email_all(to_list, cc_list, bcc_list,
                          pdf_report_path, version, status, summary,
                          confluence_url, jira_url):

    if not os.path.exists(pdf_report_path):
        sys.exit(f"❌ Missing report file: {pdf_report_path}")

    msg = EmailMessage()
    msg["Subject"] = f"Test Report v{version} - {status}"
    msg["From"] = FROM_EMAIL
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if bcc_list:
        msg["Bcc"] = ", ".join(bcc_list)

    # Emoji
    emoji = "✅" if status == "PASS" else "❌"
    color = "green" if status == "PASS" else "red"

    # TEXT PART
    msg.set_content(f"""
Test Status: {status}
Summary: {summary}

Jira Test Execution:
{jira_url or 'N/A'}

Confluence Report:
{confluence_url or 'N/A'}

PDF test report (v{version}) is attached.

Regards,
QA Automation System
""")

    # HTML PART
    msg.add_alternative(f"""
    <html>
        <body style='font-family: Arial, sans-serif;'>
            <h2>{emoji} Test Result: <span style='color:{color}'>{status}</span> (v{version})</h2>

            <p><b>Summary:</b> {summary}</p>

            <h3>🔗 Jira Test Execution</h3>
            <p>{('<a href="' + jira_url + '" target="_blank">Open Test Execution</a>') if jira_url else 'No Jira URL available.'}</p>

            <h3>📄 Confluence Report</h3>
            <p>{('<a href="' + confluence_url + '" target="_blank">View Full Report in Confluence</a>') if confluence_url else 'No Confluence URL available.'}</p>

            <p>The PDF report is attached.</p>
            <p>Regards,<br><b>QA Automation System</b></p>
        </body>
    </html>
    """, subtype="html")

    # ATTACH PDF
    with open(pdf_report_path, "rb") as f:
        file_data = f.read()
        msg.add_attachment(file_data,
                           maintype="application",
                           subtype="pdf",
                           filename=os.path.basename(pdf_report_path))

    # SEND
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print("📤 Email sent successfully!")


# =============================================================
# MAIN
# =============================================================
def main():
    pdf_report_path = os.getenv("PDF_REPORT_PATH")
    if not pdf_report_path:
        sys.exit("❌ Missing PDF_REPORT_PATH env variable")

    version = os.getenv("REPORT_VERSION", "1")
    summary = os.getenv("REPORT_SUMMARY", "No summary available")
    status = os.getenv("REPORT_STATUS", "UNKNOWN")

    # URLs
    confluence_url = read_confluence_url()
    jira_url = read_jira_issue_url()

    # Email lists
    to_list  = clean_list(TO_RAW)
    cc_list  = clean_list(CC_RAW)
    bcc_list = clean_list(BCC_RAW)

    send_single_email_all(to_list, cc_list, bcc_list,
                          pdf_report_path, version, status, summary,
                          confluence_url, jira_url)


if __name__ == "__main__":
    main()
