import os
import sys
import json
import argparse
import requests
from datetime import datetime

def create_jira_execution(summary, project_key, jira_base, jira_user, jira_token, output_file):
    url = f"{jira_base}/rest/api/3/issue"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": "Test Execution"}
        }
    }

    print(f"📌 Creating Jira Test Execution in project {project_key} ...")

    response = requests.post(url, headers=headers, json=payload, auth=(jira_user, jira_token))

    if response.status_code != 201:
        print(f"❌ ERROR creating Jira Test Execution ({response.status_code})")
        print(response.text)
        sys.exit(1)

    issue_key = response.json()["key"]

    print(f"✅ Jira Test Execution created: {issue_key}")

    # Save to file for next pipeline stage
    with open(output_file, "w") as f:
        f.write(issue_key.strip())

    print(f"💾 Saved issue key → {output_file}")

    return issue_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Jira Test Execution")
    parser.add_argument("--project", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", default="rtm_jira_issue.txt")

    args = parser.parse_args()

    jira_base = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not jira_base or not jira_user or not jira_token:
        print("❌ Missing Jira environment variables.")
        sys.exit(1)

    create_jira_execution(
        summary=args.summary,
        project_key=args.project,
        jira_base=jira_base,
        jira_user=jira_user,
        jira_token=jira_token,
        output_file=args.output
    )
