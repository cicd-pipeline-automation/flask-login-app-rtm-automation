#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests

def create_issue(jira_base, user, token, project, summary, output_file):
    url = f"{jira_base}/rest/api/3/issue"
    headers = {"Content-Type": "application/json"}

    # Team-managed project requires issueType ID (NOT name)
    TASK_ISSUE_TYPE_ID = "10091"

    payload = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"id": TASK_ISSUE_TYPE_ID}
        }
    }

    print(f"📘 Creating Jira Task issue in project {project}...")
    response = requests.post(
        url, headers=headers, auth=(user, token), data=json.dumps(payload)
    )

    if response.status_code not in (200, 201):
        print(f"❌ Jira issue creation failed ({response.status_code})")
        print(response.text)
        sys.exit(1)

    data = response.json()
    issue_key = data["key"]

    print(f"✅ Created Jira Issue: {issue_key}")

    with open(output_file, "w") as f:
        f.write(issue_key)

    print(f"📁 Saved Jira Issue Key → {output_file}")
    return issue_key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    jira_base = os.environ.get("JIRA_URL")
    jira_user = os.environ.get("JIRA_USER")
    jira_token = os.environ.get("JIRA_API_TOKEN")

    if not jira_base or not jira_user or not jira_token:
        print("❌ Missing JIRA_URL, JIRA_USER, or JIRA_API_TOKEN environment variables")
        sys.exit(1)

    create_issue(
        jira_base=jira_base,
        user=jira_user,
        token=jira_token,
        project=args.project,
        summary=args.summary,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
