#!/usr/bin/env python3
import os
import smtplib
from email.message import EmailMessage
import re

# ==============================
# Files
# ==============================
REPORT_DIR = "report"
VERSION_FILE = f"{REPORT_DIR}/version.txt"
PYTEST_LOG = f"{REPORT_DIR}/pytest_output.txt"
CONF_LINK_FILE = f"{REPORT_DIR}/confluence_url.txt"

# ==============================
# SMTP
# ==============================
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("REPORT_FROM")

# Recipients
def parse_list(x):
    if not x:
        return []
    return [i.strip() for i in re.split("[;,]", x) if i.strip()]

TO = parse_list(os.getenv("REPORT_TO", ""))
CC = parse_list(os.getenv("REPORT_CC", ""))
BCC = parse_list(os.getenv("REPORT_BCC", ""))

# ==============================
# Read version
# ==============================
def read_version():
    if not os.path.exists(VERSION_FILE):
        return 1
    try:
        with open(VERSION_FILE) as f:
            return int(f.read().strip())
    except:
        return 1

# ==============================
# Test Summary Extraction
# ==============================
def extract_summary():
    """Reads pytest_output.txt and determines:
       - passed, failed, errors, skipped
       - PASS/FAIL status
       - formatted summary string
    """

    if not os.path.exists(PYTEST_LOG):
        return "UNKNOWN", "⚪ No pytest_output.txt found"

    text = open(PYTEST_LOG, encoding="utf-8", errors="ignore").read()

    passed  = int(re.search(r"(\d+)\s+passed",  text or "", re.I).group(1)) if "passed"  in text else 0
    failed  = int(re.search(r"(\d+)\s+failed",  text or "", re.I).group(1)) if "failed"  in text else 0
    errors  = int(re.search(r"(\d+)\s+errors?", text or "", re.I).group(1)) if "error"   in text else 0
    skipped = int(re.search(r"(\d+)\s+skipped", text or "", re.I).group(1)) if "skipped" in text else 0

    total = passed + failed + errors + skipped
    rate = (passed * 100 / total) if total > 0 else 0

    status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    emoji = "✅" if status == "PASS" else "❌"

    summary = (
        f"{emoji} {passed} passed, ❌ {failed} failed, ⚠️ {errors} errors, "
        f"⏭ {skipped} skipped — Pass rate: {rate:.1f}%"
    )

    return status, summary

# ==============================
# Confluence Link (optional)
# ==============================
def read_confluence_url():
    if os.path.exists(CONF_LINK_FILE):
        return open(CONF_LINK_FILE).read().strip()
    return ""

# ==============================
# Send Email
# ==============================
def send_email(pdf_path, version, status, summary, conf_url):

    emoji = "✅" if status == "PASS" else "❌"

    msg = EmailMessage()
    msg["Subject"] = f"{emoji} Test Result {status} (v{version})"
    msg["From"] = FROM_EMAIL
    msg["To"] = ", ".join(TO)
    if CC:
        msg["Cc"] = ", ".join(CC)
    recipients = TO + CC + BCC

    # TEXT fallback
    msg.set_content(f"""Test Status: {status}
Summary: {summary}

Confluence Report:
{conf_url}

PDF Report attached.
""")

    # HTML body
    msg.add_alternative(f"""
        <html>
            <body style="font-family:Arial;">
                <h2>{emoji} Test Result: <span style='color:green'>{status}</span> (v{version})</h2>

                <p><b>Summary:</b> {summary}</p>

                <h3>📄 Confluence Report</h3>
                {'<a href="'+conf_url+'" target="_blank">View full report in Confluence</a>' if conf_url else 'No Confluence link.'}

                <p>The PDF report is attached.</p>

                <p>Regards,<br><b>QA Automation System</b></p>
            </body>
        </html>
    """, subtype="html")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                           filename=os.path.basename(pdf_path))

    print("📤 Sending email...")
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    if SMTP_PORT == 587:
        s.starttls()
    if SMTP_USER and SMTP_PASS:
        s.login(SMTP_USER, SMTP_PASS)
    s.send_message(msg, to_addrs=recipients)
    s.quit()

    print("✅ Email sent successfully")

# ==============================
# MAIN
# ==============================
def main():

    version = read_version()
    pdf_path = f"{REPORT_DIR}/test_result_report_v{version}.pdf"

    if not os.path.exists(pdf_path):
        raise SystemExit(f"❌ PDF not found: {pdf_path}")

    # Extract summary automatically (NO Jenkins dependency)
    status, summary = extract_summary()

    conf_url = read_confluence_url()

    send_email(pdf_path, version, status, summary, conf_url)

if __name__ == "__main__":
    main()
