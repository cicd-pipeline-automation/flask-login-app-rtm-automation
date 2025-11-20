#!/usr/bin/env python3
import os
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth

# --------------------------------------------------------
#  🎯 Auto-detect Test Execution Issue Type Script
# --------------------------------------------------------

def find_issue_type(jira_url, auth, project_key):
    """
    Auto-detects the correct Test Execution issue type from Jira.
    Searches for:
    - "Test Execution"
    - "RTM Test Execution"
    - Anything containing the words "Execution" or "Test"
    """

    print("\n🔍 Fetching available issue types for project:", project_key)

    meta_url = f"{jira_url}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes"
    resp = requests.get(meta_url, auth=auth)

    if resp.status_code != 200:
        print(f"❌ ERROR fetching issue types ({resp.status_code})")
        print(resp.text)
        return None

    data = resp.json()
    issue_types = data["projects"][0]["issuetypes"]

    print("📘 Available Issue Types:")
    for it in issue_types:
        print(f"   - {it['name']}")

    # Priority search terms
    preferred = [
        "RTM Test Execution",
        "Test Execution",
        "Execution"
    ]

    # 1️⃣ Try exact preferred matches
    for p in preferred:
        for it in issue_types:
            if it["name"].lower() == p.lower():
                print(f"\n✅ Selected IssueType (exact match): {it['name']}")
                return it["name"]

    # 2️⃣ Try partial match
    for it in issue_types:
        if "execution" in it["name"].lower():
            print(f"\n✅ Selected IssueType (partial match): {it['name']}")
            return it["name"]

    print("\n❌ No valid Test Execution issue type found.")
    print("   Please check Jira project configuration.\n")
    return None


def create_issue(jira_url, auth, project_key, summary, issuetype_name, output_file):
    """
    Creates the Jira issue with detected issuetype.
    """

    print("\n📝 Creating Jira Test Execution...")
    print("🔗 URL       :", f"{jira_url}/rest/api/3/issue")
    print("📘 Project   :", project_key)
    print("📘 Summary   :", summary)
    print("📘 IssueType :", issuetype_name)

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issuetype_name},
        }
    }

    resp = requests.post(
        f"{jira_url}/rest/api/3/issue",
        headers={"Content-Type": "application/json"},
        auth=auth,
        data=json.dumps(payload)
    )

    if resp.status_code not in (200, 201):
        print(f"\n❌ ERROR creating Jira Test Execution ({resp.status_code})")
        print(resp.text)
        return None

    issue_key = resp.json()["key"]

    with open(output_file, "w") as f:
        f.write(issue_key)

    print(f"\n🎉 Created Jira Test Execution: {issue_key}")
    print(f"📄 Saved to {output_file}")

    return issue_key


# --------------------------------------------------------
#  🔧 MAIN
# --------------------------------------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_API_TOKEN")

    auth = HTTPBasicAuth(jira_user, jira_token)

    # Auto-detect Test Execution issue type
    issuetype = find_issue_type(jira_url, auth, args.project)

    if not issuetype:
        print("\n🚨 Could NOT determine valid IssueType for Test Execution.")
        exit(1)

    # Create Jira issue
    result = create_issue(
        jira_url=jira_url,
        auth=auth,
        project_key=args.project,
        summary=args.summary,
        issuetype_name=issuetype,
        output_file=args.output
    )

    if not result:
        exit(1)

    print("\n✅ Jira Test Execution created successfully!")
