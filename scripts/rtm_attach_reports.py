#!/usr/bin/env python3
import os
import sys
import argparse
import requests

# ==============================================
#  Jira Attachments API — Production Ready
# ==============================================

def attach_file_to_jira(issue_key, file_path, jira_url, jira_user, jira_token):
    """
    Uploads a file to Jira issue via REST API.
    """

    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found → {file_path}")
        return False

    url = f"{jira_url}/rest/api/3/issue/{issue_key}/attachments"
    headers = {
        "X-Atlassian-Token": "no-check"
    }

    print(f"\n📄 Uploading attachment → {os.path.basename(file_path)}")
    print(f"🔗 Jira API → {url}")

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        response = requests.post(url, headers=headers, files=files, auth=(jira_user, jira_token))

    if response.status_code == 200 or response.status_code == 201:
        print(f"✅ Uploaded successfully → {os.path.basename(file_path)}")
        return True
    else:
        print(f"❌ Upload failed ({response.status_code}) → {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Attach PDF/HTML Reports to Jira Test Execution")
    parser.add_argument("--issueKey", required=True, help="Jira Issue Key (ex: RT-78)")
    parser.add_argument("--pdf", required=True, help="Path to PDF report")
    parser.add_argument("--html", required=True, help="Path to HTML report")

    args = parser.parse_args()
    issue_key = args.issueKey
    pdf_file = args.pdf
    html_file = args.html

    print(f"\n🚀 Attaching reports to Jira Issue: {issue_key}")

    # Read Jira environment variables
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not jira_url or not jira_user or not jira_token:
        print("❌ ERROR: Missing Jira environment variables.")
        sys.exit(1)

    print(f"\n🔧 Jira Base URL: {jira_url}")
    print(f"👤 Jira User: {jira_user}")

    success = True

    # Attach PDF
    if not attach_file_to_jira(issue_key, pdf_file, jira_url, jira_user, jira_token):
        success = False

    # Attach HTML
    if not attach_file_to_jira(issue_key, html_file, jira_url, jira_user, jira_token):
        success = False

    if not success:
        print("\n❌ ERROR: One or more attachments failed.")
        sys.exit(1)

    print("\n🎉 All attachments uploaded successfully to Jira!")
    sys.exit(0)


if __name__ == "__main__":
    main()
