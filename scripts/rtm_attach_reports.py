#!/usr/bin/env python3
import os
import argparse
import requests
import sys

# ================================================================
# Safely attach a file to Jira Issue
# ================================================================
def attach_file(jira_base, jira_user, jira_token, issue_key, file_path):
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found → {file_path}")
        return False

    jira_base = jira_base.rstrip("/")
    url = f"{jira_base}/rest/api/3/issue/{issue_key}/attachments"

    print(f"📎 Uploading attachment → {os.path.basename(file_path)}")
    headers = {
        "X-Atlassian-Token": "no-check",
        "Accept": "application/json"
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(
                url,
                headers=headers,
                auth=(jira_user, jira_token),
                files=files,
                timeout=30
            )
    except Exception as e:
        print(f"❌ EXCEPTION during upload → {e}")
        return False

    if response.status_code in (200, 201):
        print(f"✅ SUCCESS: Uploaded {os.path.basename(file_path)}")
        return True

    print(f"❌ Jira Upload FAILED ({response.status_code}) → {response.text}")
    return False


# ================================================================
# Main Script
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Attach PDF/HTML reports to Jira Test Execution")
    parser.add_argument("--pdf", required=True, help="Path to PDF report")
    parser.add_argument("--html", required=True, help="Path to HTML report")
    args = parser.parse_args()

    # ------------------------------------------------------------
    # Load Jira credentials (Required)
    # ------------------------------------------------------------
    jira_base = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not jira_base or not jira_user or not jira_token:
        print("❌ ERROR: Missing Jira environment variables (JIRA_URL / JIRA_USER / JIRA_API_TOKEN)")
        sys.exit(1)

    # ------------------------------------------------------------
    # Load RTM Execution Key
    # Priority:
    # 1. Env variable: RTM_EXECUTION_KEY
    # 2. File fallback: rtm_execution_key.txt
    # ------------------------------------------------------------
    issue_key = os.getenv("RTM_EXECUTION_KEY")

    if not issue_key:
        if not os.path.exists("rtm_execution_key.txt"):
            print("❌ ERROR: Missing rtm_execution_key.txt and no RTM_EXECUTION_KEY environment variable found.")
            sys.exit(1)

        with open("rtm_execution_key.txt", "r") as f:
            issue_key = f.read().strip()

    if not issue_key:
        print("❌ ERROR: RTM Execution issue key is EMPTY")
        sys.exit(1)

    print(f"🚀 Jira Test Execution Issue: {issue_key}")

    # ------------------------------------------------------------
    # Attach PDF & HTML
    # ------------------------------------------------------------
    print("\n📤 Attaching files to Jira Test Execution...\n")

    pdf_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.pdf)
    html_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.html)

    # Fail Jenkins pipeline if any upload fails
    if not (pdf_ok and html_ok):
        print("\n❌ ERROR: One or more attachments failed.")
        sys.exit(1)

    print("\n✅ All attachments uploaded successfully 🎉")
    sys.exit(0)


# ================================================================
# Entry point
# ================================================================
if __name__ == "__main__":
    main()
