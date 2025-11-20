#!/usr/bin/env python3
import os
import argparse
import requests
import json
import time
import sys


# ============================================================
# CLI parsing
# ============================================================
def parse_args():
    p = argparse.ArgumentParser(description="Upload test results ZIP to RTM")
    p.add_argument("--archive", required=True, help="ZIP file with test results")
    p.add_argument("--rtm-base", required=True, help="RTM base URL, e.g. https://rtm.example.com")
    p.add_argument("--project", required=True, help="RTM Project Key")
    p.add_argument("--job-url", required=True, help="Jenkins BUILD_URL (must start with http/https)")
    return p.parse_args()


# ============================================================
# Main Script
# ============================================================
def main():
    args = parse_args()

    # ------------------------
    # Validate RTM token
    # ------------------------
    token = os.getenv("RTM_API_TOKEN")
    if not token:
        print("❌ ERROR: Missing RTM_API_TOKEN environment variable")
        sys.exit(1)

    # ------------------------
    # Validate job url format
    # ------------------------
    if not args.job_url.startswith(("http://", "https://")):
        print("❌ ERROR: job-url must start with http:// or https://")
        sys.exit(1)

    # Sanitize RTM base
    rtm_base = args.rtm_base.rstrip("/")

    import_url = f"{rtm_base}/api/v2/automation/import-test-results"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    print("🚀 Starting RTM upload...")

    # ------------------------
    # Upload ZIP to RTM
    # ------------------------
    try:
        with open(args.archive, "rb") as f:
            files = {"file": f}
            data = {
                "projectKey": args.project,
                "reportType": "JUNIT",
                "jobUrl": args.job_url
            }
            response = requests.post(
                import_url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
    except Exception as e:
        print(f"❌ ERROR: Exception during upload → {e}")
        sys.exit(1)

    # ------------------------
    # Handle Upload Response
    # ------------------------
    if response.status_code not in (200, 202):
        print("❌ ERROR: RTM Upload Failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
        sys.exit(1)

    # Task ID can come as text OR JSON
    try:
        try:
            task_id = response.json().get("taskId")
        except:
            task_id = response.text.strip()
    except Exception:
        print("❌ ERROR: Cannot extract task ID from RTM response")
        sys.exit(1)

    if not task_id:
        print("❌ ERROR: RTM did not return a valid task ID")
        sys.exit(1)

    print(f"📌 RTM Task ID: {task_id}")

    status_url = f"{rtm_base}/api/v2/automation/import-status/{task_id}"

    # ------------------------
    # Poll RTM import status
    # ------------------------
    print("\n⏳ Checking import status...\n")

    while True:
        try:
            resp = requests.get(status_url, headers=headers, timeout=30)
            data = resp.json()
        except Exception as e:
            print(f"❌ ERROR fetching import status → {e}")
            sys.exit(1)

        status = data.get("status")
        progress = data.get("progress", 0)

        print(f"➡️  Status: {status} (Progress: {progress}%)")

        if status in ("FAILED", "ERROR"):
            print("❌ RTM Import Failed")
            print(json.dumps(data, indent=2))
            sys.exit(1)

        if status != "IMPORTING":
            break

        time.sleep(2)

    print("\n🎉 RTM Import Complete:")
    print(json.dumps(data, indent=2))

    # ------------------------
    # Capture RTM Execution Key
    # ------------------------
    test_execution_key = data.get("testExecutionKey")

    if not test_execution_key:
        print("⚠️ WARNING: No testExecutionKey returned by RTM.")
        sys.exit(0)

    # Validate format (optional)
    if not test_execution_key.startswith(("RT-", "TE-", "TEST-")):
        print(f"⚠️ WARNING: testExecutionKey has unusual format ({test_execution_key})")

    # Save to file for next stage (rtm_attach_reports.py)
    try:
        with open("rtm_execution_key.txt", "w") as f:
            f.write(test_execution_key)
        print(f"📝 Saved → rtm_execution_key.txt ({test_execution_key})")
    except Exception as e:
        print(f"❌ ERROR writing rtm_execution_key.txt → {e}")
        sys.exit(1)

    print("✅ RTM Upload script completed successfully.")
    sys.exit(0)


# ============================================================
# Entry
# ============================================================
if __name__ == "__main__":
    main()
