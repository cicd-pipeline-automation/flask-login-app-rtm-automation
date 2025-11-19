#!/usr/bin/env python3
import os, sys, time, json, argparse, requests
from pathlib import Path

def args():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True)
    p.add_argument("--rtm-base", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--report-type", default="JUNIT")
    p.add_argument("--test-exec")
    return p.parse_args()

def main():
    a = args()
    a.rtm_base = a.rtm_base.rstrip("/")

    token = os.getenv("RTM_API_TOKEN")
    if not token:
        sys.exit("❌ RTM_API_TOKEN missing in Jenkins environment!")

    archive = Path(a.archive)
    if not archive.exists():
        sys.exit(f"❌ Archive file not found: {archive}")

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{a.rtm_base}/api/v2/automation/import-test-results"

    data = {
        "projectKey": a.project,
        "reportType": a.report_type,
        "jobUrl": os.getenv("BUILD_URL", "")
    }

    if a.test_exec:
        data["testExecutionKey"] = a.test_exec

    print("🚀 Uploading results to RTM...")

    with archive.open("rb") as f:
        files = {"file": f}
        r = requests.post(url, headers=headers, data=data, files=files)

    if r.status_code >= 400:
        print("❌ RTM Upload Failed")
        print("Status:", r.status_code)
        print("Response:", r.text)
        sys.exit(1)

    task_id = r.text.strip()
    print(f"📌 RTM Task ID: {task_id}")

    # Poll status
    status_url = f"{a.rtm_base}/api/v2/automation/import-status/{task_id}"

    MAX_WAIT = 300
    start = time.time()

    while True:
        if time.time() - start > MAX_WAIT:
            sys.exit("⏱ Timeout waiting for RTM import to finish.")

        rr = requests.get(status_url, headers=headers)
        rr.raise_for_status()
        status = rr.json()

        print(f"➡️ RTM Status: {status.get('status')} Progress: {status.get('progress', 'N/A')}")

        if status.get("status") != "IMPORTING":
            print("🎉 Import complete:", json.dumps(status, indent=2))
            break

        time.sleep(3)

if __name__ == "__main__":
    main()
