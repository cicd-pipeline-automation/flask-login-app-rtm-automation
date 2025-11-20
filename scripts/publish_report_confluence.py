#!/usr/bin/env python3
import os
import sys
import time
import datetime
import json
import re
import requests
from requests.auth import HTTPBasicAuth

# =============================================================
# Environment Variables
# =============================================================
CONFLUENCE_BASE  = os.getenv('CONFLUENCE_BASE', '').rstrip('/')
CONFLUENCE_USER  = os.getenv('CONFLUENCE_USER')
CONFLUENCE_TOKEN = os.getenv('CONFLUENCE_TOKEN')
CONFLUENCE_SPACE = os.getenv('CONFLUENCE_SPACE')
CONFLUENCE_TITLE = os.getenv('CONFLUENCE_TITLE', 'Test Result Report')

REPORT_DIR   = 'report'
VERSION_FILE = os.path.join(REPORT_DIR, 'version.txt')
BASE_NAME    = 'test_result_report'
PYTEST_LOG   = os.path.join(REPORT_DIR, 'pytest_output.txt')

auth = HTTPBasicAuth(CONFLUENCE_USER, CONFLUENCE_TOKEN)
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Atlassian-Token": "no-check"
}

# =============================================================
# Validation
# =============================================================
def validate_env():
    missing = []
    for k, v in {
        "CONFLUENCE_BASE": CONFLUENCE_BASE,
        "CONFLUENCE_USER": CONFLUENCE_USER,
        "CONFLUENCE_TOKEN": CONFLUENCE_TOKEN,
        "CONFLUENCE_SPACE": CONFLUENCE_SPACE,
        "CONFLUENCE_TITLE": CONFLUENCE_TITLE
    }.items():
        if not v:
            missing.append(k)
    if missing:
        sys.exit(f"❌ Missing required environment variables: {', '.join(missing)}")

    if "/rest/api" in CONFLUENCE_BASE:
        sys.exit("❌ CONFLUENCE_BASE must NOT contain '/rest/api'. Use: https://company.atlassian.net/wiki")

# =============================================================
# Read version
# =============================================================
def read_version():
    if os.path.exists(VERSION_FILE):
        try:
            return int(open(VERSION_FILE).read().strip())
        except:
            return 1
    return 1

# =============================================================
# Extract test summary
# =============================================================
def extract_test_summary():
    if not os.path.exists(PYTEST_LOG):
        return "⚪ No pytest_output.txt found.", "UNKNOWN"

    text = open(PYTEST_LOG, encoding="utf-8", errors="ignore").read()

    passed = failed = errors = skipped = 0

    if m := re.search(r"(\d+)\s+passed", text):  passed = int(m.group(1))
    if m := re.search(r"(\d+)\s+failed", text):  failed = int(m.group(1))
    if m := re.search(r"(\d+)\s+errors?", text): errors = int(m.group(1))
    if m := re.search(r"(\d+)\s+skipped", text): skipped = int(m.group(1))

    total = passed + failed + errors + skipped
    rate = (passed / total * 100) if total else 0

    status = "PASS" if failed == 0 and errors == 0 else "FAIL"
    emoji = "✅" if status == "PASS" else "❌"

    summary = (
        f"{emoji} {passed} passed | ❌ {failed} failed | ⚠️ {errors} errors | "
        f"⏭ {skipped} skipped — Pass rate: {rate:.1f}%"
    )

    return summary, status

# =============================================================
# Create Confluence Page
# =============================================================
def create_page(title, html_body):
    url = f"{CONFLUENCE_BASE}/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE},
        "body": {
            "storage": {"value": html_body, "representation": "storage"}
        }
    }
    print(f"🌐 Creating Confluence page: {title}")
    r = requests.post(url, headers=headers, json=payload, auth=auth)
    if not r.ok:
        print(f"❌ Page creation failed ({r.status_code})")
        print(r.text)
        sys.exit(1)

    return r.json()["id"]

# =============================================================
# Upload Attachment
# =============================================================
def upload_attachment(page_id, file_path):
    if not os.path.exists(file_path):
        sys.exit(f"❌ Attachment missing: {file_path}")

    file_name = os.path.basename(file_path)

    mime_type = (
        "text/html; charset=utf-8"
        if file_name.lower().endswith(".html") else
        "application/pdf"
    )

    url = (
        f"{CONFLUENCE_BASE}/rest/api/content/"
        f"{page_id}/child/attachment?allowDuplicated=true"
    )

    print(f"📤 Uploading: {file_name}")

    backoff = [2,4,6,10,15,20,30]

    for attempt, delay in enumerate(backoff, start=1):
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, mime_type)}

                r = requests.post(url,
                                  files=files,
                                  headers={"X-Atlassian-Token": "no-check"},
                                  auth=auth,
                                  timeout=60)

            if r.status_code in (200, 201):
                print(f"📎 Uploaded: {file_name}")
                return file_name

            print(f"⚠️ Attempt {attempt}/{len(backoff)} failed: {r.status_code}")
            print(r.text)
            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Exception: {e}")
            time.sleep(delay)

    sys.exit(f"❌ Attachment upload failed permanently → {file_name}")

# =============================================================
# Update Page Version
# =============================================================
def get_page_version(page_id):
    url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}?expand=version"
    r = requests.get(url, auth=auth)
    if not r.ok:
        print(f"❌ Failed fetching page version: {r.status_code}")
        print(r.text)
        sys.exit(1)
    return r.json()["version"]["number"]

# =============================================================
# Main Logic
# =============================================================
def main():
    validate_env()

    version = read_version()
    pdf_path  = os.path.join(REPORT_DIR, f"{BASE_NAME}_v{version}.pdf")
    html_path = os.path.join(REPORT_DIR, f"{BASE_NAME}_v{version}.html")

    if not os.path.exists(pdf_path) or not os.path.exists(html_path):
        sys.exit("❌ Required report files missing!")

    summary, status = extract_test_summary()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_time = timestamp.replace(":", "-")

    emoji = "✅" if status == "PASS" else "❌"
    color = "green" if status == "PASS" else "red"

    title = f"{CONFLUENCE_TITLE} v{version} ({status}) - {safe_time}"

    html = f"""
        <h2>{emoji} Test Report v{version}</h2>
        <p><b>Date:</b> {timestamp}</p>
        <p><b>Status:</b> <span style="color:{color};font-weight:bold">{status}</span></p>
        <p><b>Summary:</b> {summary}</p>
        <p>Attachments are available below.</p>
    """

    page_id = create_page(title, html)

    # Upload attachments
    pdf_name = upload_attachment(page_id, pdf_path)
    html_name = upload_attachment(page_id, html_path)

    pdf_link  = f"{CONFLUENCE_BASE}/download/attachments/{page_id}/{pdf_name}"
    html_link = f"{CONFLUENCE_BASE}/download/attachments/{page_id}/{html_name}"

    # Update page with download links
    new_html = html + f"""
        <h3>📎 Attachments</h3>
        <p><a href="{html_link}">{html_name}</a></p>
        <p><a href="{pdf_link}">{pdf_name}</a></p>
    """

    current_ver = get_page_version(page_id)

    update_url = f"{CONFLUENCE_BASE}/rest/api/content/{page_id}"
    update_payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": current_ver + 1},
        "body": {
            "storage": {
                "value": new_html,
                "representation": "storage"
            }
        }
    }

    r = requests.put(update_url, headers=headers, json=update_payload, auth=auth)
    if not r.ok:
        print(f"❌ Page update failed: {r.status_code}")
        print(r.text)
        sys.exit(1)

    # Correct Cloud URL slug
    page_url = f"{CONFLUENCE_BASE}/spaces/{CONFLUENCE_SPACE}/pages/{page_id}"

    print(f"\n✅ Published to Confluence: {page_url}")
    print(f"🔗 PDF Link:  {pdf_link}")
    print(f"🔗 HTML Link: {html_link}\n")

    # Save URL for email script
    with open(os.path.join(REPORT_DIR, "confluence_url.txt"), "w") as f:
        f.write(page_url)

    print(f"📁 Saved page URL → report/confluence_url.txt")

# =============================================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        sys.exit(1)
