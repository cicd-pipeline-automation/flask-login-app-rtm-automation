import os
import argparse
import requests
import sys
import json
import time


def info(msg): print(f"ℹ {msg}")
def success(msg): print(f"✅ {msg}")
def error(msg): print(f"❌ {msg}")
def warn(msg): print(f"⚠ {msg}")


# -------------------------
# Parse CLI args
# -------------------------
parser = argparse.ArgumentParser(description="Attach HTML/PDF reports to Jira")
parser.add_argument("--issueKey", required=True, help="Jira issue key (e.g., RT-72)")
parser.add_argument("--pdf", required=True, help="PDF file path")
parser.add_argument("--html", required=True, help="HTML file path")
args = parser.parse_args()

issue_key = args.issueKey.strip()
pdf_file = args.pdf
html_file = args.html

# -------------------------
# Validate report files
# -------------------------
if not os.path.isfile(pdf_file):
    error(f"PDF file not found: {pdf_file}")
    sys.exit(1)

if not os.path.isfile(html_file):
    error(f"HTML file not found: {html_file}")
    sys.exit(1)

# -------------------------
# Jira credentials
# -------------------------
JIRA_BASE = os.getenv("JIRA_URL")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

missing = []
if not JIRA_BASE: missing.append("JIRA_URL")
if not JIRA_USER: missing.append("JIRA_USER")
if not JIRA_TOKEN: missing.append("JIRA_API_TOKEN")

if missing:
    error(f"Missing Jira env vars: {', '.join(missing)}")
    sys.exit(1)

upload_url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}/attachments"
auth = (JIRA_USER, JIRA_TOKEN)
headers = {"X-Atlassian-Token": "no-check"}

info(f"Jira Issue: {issue_key}")
info(f"Upload URL: {upload_url}\n")


# -------------------------
# Upload helper with retry
# -------------------------
def upload_with_retry(filepath, retries=3, delay=2):
    filename = os.path.basename(filepath)
    info(f"📤 Uploading → {filename}")

    for attempt in range(1, retries + 1):
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                resp = requests.post(upload_url, auth=auth, headers=headers, files=files)

            if resp.status_code in (200, 201):
                success(f"Uploaded: {filename}")
                return True

            try:
                msg = json.dumps(resp.json(), indent=2)
            except:
                msg = resp.text

            warn(f"Attempt {attempt}/{retries} failed → {resp.status_code}\n{msg}")

            if attempt < retries:
                time.sleep(delay)
                info("Retrying...")

        except Exception as e:
            warn(f"Exception: {e}")
            if attempt < retries:
                time.sleep(delay)

    error(f"Failed after {retries} attempts → {filename}")
    return False


# -------------------------
# Upload both files
# -------------------------
pdf_ok = upload_with_retry(pdf_file)
html_ok = upload_with_retry(html_file)

if not (pdf_ok and html_ok):
    error("Attachment process failed.")
    sys.exit(1)

success("All attachments uploaded successfully!")
sys.exit(0)
