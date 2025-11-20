#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================
 📘 CREATE JIRA TEST EXECUTION ISSUE
----------------------------------------------------------------
 This script creates a Jira Test Execution issue and stores the
 resulting issue key into 'rtm_jira_issue.txt' for the pipeline.

 ➤ Requirements:
   - ENV: JIRA_URL
   - ENV: JIRA_USER
   - ENV: JIRA_API_TOKEN
   - pip install requests

 ➤ Example:
   python create_jira_execution.py \
        --project RT \
        --summary "Automated Test Execution - Build 41" \
        --output rtm_jira_issue.txt
================================================================
"""

import os
import sys
import json
import argparse
import requests

# ----------------------------------------------------------------
# Load Required Environment Variables
# ----------------------------------------------------------------
JIRA_URL       = os.getenv("JIRA_URL")
JIRA_USER      = os.getenv("JIRA_USER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

REQUIRED_ENV = {
    "JIRA_URL": JIRA_URL,
    "JIRA_USER": JIRA_USER,
    "JIRA_API_TOKEN": JIRA_API_TOKEN,
}

for key, value in REQUIRED_ENV.items():
    if not value:
        print(f"❌ ERROR: Missing required environment variable: {key}")
        sys.exit(1)

# Ensure base URL has no trailing slash
JIRA_URL = JIRA_URL.rstrip("/")


# ----------------------------------------------------------------
# Parse Arguments
# ----------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Create a Jira Test Execution Issue"
)

parser.add_argument("--project", required=True, help="Jira Project Key")
parser.add_argument("--summary", required=True, help="Issue Summary")
parser.add_argument("--description", default="Automated Test Execution run via Jenkins Pipeline",
                    help="Issue Description")
parser.add_argument("--output", required=True, help="File to write the Jira Issue Key")

args = parser.parse_args()


# ----------------------------------------------------------------
# Prepare Jira Payload (Xray Test Execution or Custom Issue Type)
# ----------------------------------------------------------------
# 🔥 If your Jira uses Xray:
ISSUE_TYPE_NAME = "Test Execution"

payload = {
    "fields": {
        "project": {"key": args.project},
        "summary": args.summary,
        "description": args.description,
        "issuetype": {"name": ISSUE_TYPE_NAME}
    }
}

# ----------------------------------------------------------------
# Send Request
# ----------------------------------------------------------------
api_url = f"{JIRA_URL}/rest/api/3/issue"

print("\n📘 Creating Jira Test Execution...")
print(f"🔗 URL       : {api_url}")
print(f"📁 Project   : {args.project}")
print(f"📝 Summary   : {args.summary}")
print(f"🧩 IssueType : {ISSUE_TYPE_NAME}\n")

try:
    response = requests.post(
        api_url,
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        auth=(JIRA_USER, JIRA_API_TOKEN)
    )
except Exception as e:
    print(f"❌ ERROR: Exception during Jira API call: {e}")
    sys.exit(1)


# ----------------------------------------------------------------
# Handle Jira API Response
# ----------------------------------------------------------------
if response.status_code not in (200, 201):
    print(f"❌ ERROR creating Jira Test Execution ({response.status_code})")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    sys.exit(1)

result = response.json()
issue_key = result.get("key")

if not issue_key:
    print("❌ ERROR: Jira returned success but no issue key in response")
    print(result)
    sys.exit(1)

print(f"✅ SUCCESS: Jira Test Execution created → {issue_key}")


# ----------------------------------------------------------------
# Save Jira Issue Key to File
# ----------------------------------------------------------------
try:
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(issue_key)
except Exception as e:
    print(f"❌ ERROR writing to file {args.output}: {e}")
    sys.exit(1)

print(f"💾 Saved Jira Test Execution Key → {args.output}")
print("\n🎉 Jira Issue Creation Completed Successfully!\n")
