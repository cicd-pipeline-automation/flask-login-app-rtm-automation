#!/usr/bin/env python3
import os
import argparse
import requests
import json
import time


def parse_args():
    p = argparse.ArgumentParser(description="Upload test results to RTM")
    p.add_argument("--archive", required=True)
    p.add_argument("--rtm-base", required=True)
    p.add_argument("--project", required=True)
    return p.parse_args()


def main():
    args = parse_args()

    token = os.getenv("RTM_API_TOKEN")
    if not token:
        raise SystemExit("❌ Missing RTM_API_TOKEN environment variable")

    url = f"{args.rtm_base}/api/v2/automation/import-test-results"
    headers = {"Authorization": f"Bearer {token}"}

    print("🚀 Uploading ZIP to RTM...")

    with open(args.archive, "rb") as f:
        files = {"file": f}
        data = {
            "projectKey": args.project,
            "reportType": "JUNIT",
            "jobUrl": os.getenv("CI_JOB_URL", "N/A")
        }
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        print("❌ RTM Upload Failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
        return

    task_id = response.text.strip()
    print(f"📌 RTM Task ID: {task_id}")

    # Check status
    status_url = f"{args.rtm_base}/api/v2/automation/import-status/{task_id}"

    while True:
        resp = requests.get(status_url, headers=headers)
        data = resp.json()
        print(f"➡️  RTM Status: {data.get('status')} Progress: {data.get('progress')}")

        if data.get("status") != "IMPORTING":
            break
        time.sleep(2)

    print("🎉 Import complete:", json.dumps(data, indent=2))

    # Save created test execution key
    test_exec = data.get("testExecutionKey")
    if not test_exec:
        print("⚠ No testExecutionKey returned, cannot write file.")
        return

    with open("rtm_execution_key.txt", "w") as f:
        f.write(test_exec)

    print(f"📝 RTM execution key saved -> rtm_execution_key.txt ({test_exec})")


if __name__ == "__main__":
    main()
