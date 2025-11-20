#!/usr/bin/env python3
import os
import argparse
import requests


def attach_file(rtm_base, jira_user, jira_token, exec_key, file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print(f"📎 Uploading attachment → {os.path.basename(file_path)}")

    # RTM attachment API (NOT Jira issue attachment API)
    url = f"{rtm_base}/rest/atm/1.0/testexecution/{exec_key}/attachments"

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        r = requests.post(url, auth=(jira_user, jira_token), files=files)

    if r.status_code in (200, 201):
        print(f"✅ Uploaded: {os.path.basename(file_path)}")
        return True

    print(f"❌ Upload failed ({r.status_code}) → {r.text}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--html", required=True)
    args = parser.parse_args()

    rtm_base = os.getenv("RTM_BASE_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not (rtm_base and jira_user and jira_token):
        raise SystemExit("❌ Missing RTM_BASE_URL / JIRA_USER / JIRA_API_TOKEN")

    # Load RTM Execution Key
    if not os.path.exists("rtm_execution_key.txt"):
        raise SystemExit("❌ Missing rtm_execution_key.txt — RTM upload step failed")

    with open("rtm_execution_key.txt", "r") as f:
        exec_key = f.read().strip()

    print(f"🚀 Attaching reports to RTM execution: {exec_key}")

    attach_file(rtm_base, jira_user, jira_token, exec_key, args.pdf)
    attach_file(rtm_base, jira_user, jira_token, exec_key, args.html)


if __name__ == "__main__":
    main()
