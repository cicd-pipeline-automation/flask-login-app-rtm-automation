#!/usr/bin/env python3
import os
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth

# --------------------------------------------------------
#  🔍 FIXED createmeta + AUTO-DETECT ISSUE TYPE
# --------------------------------------------------------

def fetch_createmeta(jira_url, auth, project_key):
    """
    Fetch project issue type metadata from Jira Cloud.
    Handles multiple fallback attempts.
    """

    urls = [
        # Full correct API for Jira Cloud (primary)
        f"{jira_url}/rest/api/3/issue/createmeta"
        f"?projectKeys={project_key}&expand=projects.issuetypes",

        # Fallback 1 (some Jira sites require this)
        f"{jira_url}/rest/api/3/issue/createmeta?projectKeys={project_key}",

        # Fallback 2 (bare createmeta)
        f"{jira_url}/rest/api/3/issue/createmeta"
    ]

    for u in urls:
        print(f"\n🔍 Trying createmeta: {u}")
        resp = requests.get(u, auth=auth)

        # Must be valid JSON
        try:
            data = resp.json()
        except:
            print(f"⚠️ Invalid JSON response from Jira ({resp.status_code})")
            continue

        if "projects" in data and len(data["projects"]) > 0:
            print("✅ createmeta returned valid project data")
            return data

    print("\n❌ Jira createmeta returned NO usable project metadata.")
    return None


def find_issue_type(jira_url, auth, project_key):
    """Auto-detect the best issue type for Test Execution."""
    data = fetch_createmeta(jira_url, auth, project_key)

    if not data:
        print("🚨 Cannot continue — no issue types returned from Jira.")
        return None

    issue_types = data["projects"][0]["issuetypes"]

    print("\n📘 Available Issue Types:")
    for it in issue_types:
        print(f"   - {it['name']}")

    # Priority search
    preferred = [
        "RTM Test Execution",
        "Test Execution",
        "Execution"
    ]

    for pref in preferred:
        for it in issue_types:
            if it["name"].lower() == pref.lower():
                print(f"\n✅ Selected IssueType (exact match): {it['name']}")
                return it["name"]

    for it in issue_types:
        if "execution" in it["name"].lower():
            print(f"\n✅ Selected IssueType (partial match): {it['name']}")
            return it["name"]

    print("\n❌ No valid Test Execution issue type found.")
    return None


def create_issue(jira_url, auth, project_key, summary, issuetype_name, output_file):
    """Create Jira Test Execution issue."""
    print("\n📝 Creating Jira Test Execution...")
    print("📘 Using IssueType:", issuetype_name)

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
        data=json.dumps(payload),
    )

    if resp.status_code not in (200, 201):
        print(f"\n❌ ERROR creating Jira issue ({resp.status_code})")
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

    issuetype = find_issue_type(jira_url, auth, args.project)

    if not issuetype:
        print("\n🚨 Unable to determine a valid issue type. Stopping.")
        exit(1)

    result = create_issue(
        jira_url,
        auth,
        args.project,
        args.summary,
        issuetype,
        args.output
    )

    if not result:
        exit(1)

    print("\n✅ Jira Test Execution created successfully!")
