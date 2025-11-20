#!/usr/bin/env python3
import os
import argparse
import requests
import sys
import time
import re

# ================================================================
# Upload attachment to Jira with retries + better error handling
# ================================================================
def attach_file(jira_base, jira_user, jira_token, issue_key, file_path, retries=3):

    if not os.path.exists(file_path):
        print(f"❌ File not found → {file_path}")
        return False

    jira_base = jira_base.rstrip("/")
    url = f"{jira_base}/rest/api/3/issue/{issue_key}/attachments"

    print(f"\n📎 Uploading attachment → {os.path.basename(file_path)}")
    print(f"🔗 Jira API URL → {url}")

    headers = {
        "X-Atlassian-Token": "no-check",
        "Accept": "application/json"
    }

    for attempt in range(1, retries + 1):
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
            print(f"❌ Exception during upload → {e}")
            time.sleep(2)
            continue

        # -----------------------------
        # SUCCESS
        # -----------------------------
        if response.status_code in (200, 201):
            print(f"✅ SUCCESS: Uploaded {os.path.basename(file_path)}")
            return True

        # -----------------------------
        # COMMON ERROR CASES
        # -----------------------------
        if response.status_code == 401:
            print("❌ ERROR 401 → Invalid Jira username or API token")
            return False

        if response.status_code == 403:
            print("❌ ERROR 403 → Jira user does NOT have permission to upload attachments")
            return False

        if response.status_code == 404:
            print(f"❌ ERROR 404 → Issue NOT found or no access: {response.text}")
            return False

        if response.status_code == 413:
            print("❌ ERROR 413 → File too large for Jira attachment limits")
            return False

        if response.status_code == 429:
            print(f"⚠️ WARNING 429 (Rate Limit) → Retry {attempt}/{retries}")
            time.sleep(3)
            continue

        print(f"❌ Upload failed ({response.status_code}) → {response.text}")
        return False

    return False


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Attach PDF/HTML reports to Jira Test Execution")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--html", required=True)
    args = parser.parse_args()

    jira_base = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not (jira_base and jira_user and jira_token):
        print("❌ ERROR: Missing Jira environment variables (JIRA_URL, JIRA_USER, JIRA_API_TOKEN)")
        sys.exit(1)

    # ------------------------------------------------------------
    # LOAD RTM EXECUTION KEY
    # ------------------------------------------------------------
    issue_key = os.getenv("RTM_EXECUTION_KEY")

    if not issue_key:
        if not os.path.exists("rtm_execution_key.txt"):
            print("❌ ERROR: No RTM_EXECUTION_KEY and missing rtm_execution_key.txt")
            sys.exit(1)

        with open("rtm_execution_key.txt", "r") as f:
            issue_key = f.read().strip()

    # Validate format e.g. RT-70
    if not re.match(r"^[A-Z]{1,10}-\d+$", issue_key):
        print(f"❌ ERROR: Invalid Jira Issue Key format → {issue_key}")
        sys.exit(1)

    print(f"🚀 Jira Test Execution Issue: {issue_key}")

    # ------------------------------------------------------------
    # ATTACH FILES
    # ------------------------------------------------------------
    print("\n📤 Attaching files to Jira...\n")

    pdf_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.pdf)
    html_ok = attach_file(jira_base, jira_user, jira_token, issue_key, args.html)

    if not (pdf_ok and html_ok):
        print("\n❌ ERROR: One or more attachments failed.")
        sys.exit(1)

    print("\n🎉 SUCCESS: All files uploaded to Jira!")
    sys.exit(0)


if __name__ == "__main__":
    main()
