#!/usr/bin/env python3
import os
import argparse
import requests


def parse_args():
    p = argparse.ArgumentParser(description="Attach report files to RTM Test Execution")
    p.add_argument("--exec", required=True, help="RTM Test Execution key (e.g., RT-58)")
    p.add_argument("--pdf", required=True, help="Path to PDF report")
    p.add_argument("--html", required=True, help="Path to HTML report")
    return p.parse_args()


def upload_attachment(rtm_base, token, execution_key, file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    url = f"{rtm_base}/api/v2/automation/add-attachment/{execution_key}"
    headers = {"Authorization": f"Bearer {token}"}

    file_name = os.path.basename(file_path)
    print(f"📎 Uploading attachment → {file_name}")

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f)}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code in (200, 201, 204):
        print(f"✅ Uploaded: {file_name}")
        return True
    else:
        print(f"❌ Failed to upload {file_name}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    args = parse_args()

    token = os.getenv("RTM_API_TOKEN")
    rtm_base = os.getenv("RTM_BASE_URL")

    if not token or not rtm_base:
        raise SystemExit("❌ RTM_API_TOKEN or RTM_BASE_URL environment variables missing.")

    execution_key = args.exec

    print(f"🚀 Attaching reports to RTM Test Execution: {execution_key}")
    print(f"🌐 RTM Base: {rtm_base}")

    pdf_ok = upload_attachment(rtm_base, token, execution_key, args.pdf)
    html_ok = upload_attachment(rtm_base, token, execution_key, args.html)

    if pdf_ok and html_ok:
        print("🎉 All attachments uploaded successfully.")
    else:
        print("⚠ Some attachments failed.")


if __name__ == "__main__":
    main()
