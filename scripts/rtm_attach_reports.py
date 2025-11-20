#!/usr/bin/env python3

import os
import argparse
import requests
import sys
import re
import time

# ================================================================
# Retry-safe Jira attachment uploader
# ================================================================
def attach_file(jira_base, jira_user, jira_token, issue_key, file_path, retry=3):

    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found → {file_path}")
        return False

    jira_base = jira_base.rstrip("/")
    url = f"{jira_base}/rest/api/3/issue/{issue_key}/attachments"

    print(f"\n📎 Uploading attachment → {os.path.basename(file_path)}")
    print(f"🔗 Jira API URL → {url}")

    headers = {
        "X-Atlassian-Token": "no-check",
        "Accept": "application/json"
    }

    for attempt in range(1, retry + 1):
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

            # Success
            if response.status_code in (200, 201):
                print(f"✅ SUCCESS: Uploaded {os.path.basename(file_path)}")
                return True

            # Authentication issues
            if response.status_code == 401:
                print("❌ ERROR 401 — Invalid Jira username/API token")
                return False

            # Permission issue
            if response.status_code == 403:
                print("❌ ERROR 403 — User does NOT have permissions to upload attachments")
                return False

            # Issue does not exist or inaccessible
            if response.status_code == 404:
                print("❌ ERROR 404 — Issue key not found or no access:", response.text)
                return False

            # Rate limit — retry
            if response.status_code == 429:
                print(f"⚠️ 429 Rate limit hit — retrying attempt {attempt}/{retry}")
                time.sleep(3)
                continue

            # Large file error
            if response.status_code == 413:
                print("❌ ERROR 413 — File too large for Jira attachment limits")
                return False

            print(f"❌ Jira Upload FAILED ({response.status_code}) → {response.text}")
            return False

        except Exception as e:
            print(f"❌ EXCEPTION during upload → {e}")

        time.sleep(2)

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
    # Load Jira credentials
    # ------------------------------------------------------------
    jira_base = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not jira_base or not jira_user or not jira_token:
        print("❌ ERROR: Missing Jira environment variables (JIRA_URL/JIRA_USER/JIRA_API_TOKEN)")
        sys.exit(1)

    # ------------------------------------------------------------
    # Load RTM test execution issue key
    # ------------------------------------------------------------
    issue_key = os.getenv("RTM_EXECUTION_KEY")

    if not issue_key:
        if not os.path.exists("rtm_execution_key.txt"):
            print("❌ ERROR: Missing rtm_execution_key.txt and env variable")
            sys.exit(1)

        with open("rtm_execution_key.txt", "r") as f:
            issue_key = f.read().strip()

    if not re.match(r"^[A-Z]{1,10}-\d+$", issue_key):
        print(f"❌ ERROR: Invalid Jira Issue Key format → {issue_key}")
        sys.exit(1)

    print(f"🚀 Jira Test Execution Issue: {issue_key}")

    # ------------------------------------------------------------
    # Upload attachments
    # ------------------------------------------------------------
    print("\n📤 Attaching files to Jira Test Execution...\n")

    pdf_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.pdf)
    html_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.html)

    if not (pdf_ok and html_ok):
        print("\n❌ ERROR: One or more attachments failed.")
        sys.exit(1)

    print("\n🎉 SUCCESS — All attachments uploaded to Jira!")
    sys.exit(0)


if __name__ == "__main__":
    main()
