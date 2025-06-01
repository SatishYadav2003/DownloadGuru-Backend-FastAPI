# test.py
import time
import requests
import zipfile
import io
import os

# ─── CONFIG ──────────────────────────────────────────────────────────────────
GITHUB_TOKEN = "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"
REPO = "SatishYadav2003/DownloadGuru-Backend-FastAPI"
WORKFLOW_FILE = "fetch-cookies.yml"
BRANCH = "main"

GOOGLE_EMAIL = "crce.9939.ce@gmail.com"
GOOGLE_PASSWORD = "crce.9939.ce@7769030868"
# ────────────────────────────────────────────────────────────────────────────

def trigger_github_action():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "ref": BRANCH,
        "inputs": {
            "email": GOOGLE_EMAIL,
            "password": GOOGLE_PASSWORD
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 204:
        print("✅ Successfully triggered the GitHub Action.")
        return True
    else:
        print("❌ Failed to trigger workflow:", resp.status_code, resp.text)
        return False

def download_cookies_artifact():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    for attempt in range(1, 31):
        print(f"[Attempt {attempt}] Checking for 'cookies' artifact...")
        url = f"https://api.github.com/repos/{REPO}/actions/artifacts"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print("⚠️ Error listing artifacts:", resp.status_code, resp.text)
            time.sleep(5)
            continue

        data = resp.json()
        artifacts = data.get("artifacts", [])
        for art in artifacts:
            if art.get("name") == "cookies":
                artifact_id = art["id"]
                download_url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
                print("🔗 Found artifact. Downloading:", download_url)

                zresp = requests.get(download_url, headers=headers)
                if zresp.status_code == 200:
                    zfile = zipfile.ZipFile(io.BytesIO(zresp.content))
                    for member in zfile.namelist():
                        if member.endswith("cookies.txt"):
                            # Extract cookies.txt into current directory
                            zfile.extract(member, ".")
                            os.replace(member, "cookies.txt")
                            print("📂 Saved cookies.txt in this folder.")
                            return True
                else:
                    print("⚠️ Failed downloading artifact zip:", zresp.status_code, zresp.text)
                    return False

        time.sleep(5)

    print("❌ Timed out waiting for 'cookies' artifact.")
    return False

if __name__ == "__main__":
    if trigger_github_action():
        print("⏳ Waiting 5 seconds before polling for artifact…")
        time.sleep(5)
        success = download_cookies_artifact()
        if success:
            print("\n🎉 Done. You already have ./cookies.txt")
        else:
            print("\n⚠️ Could not retrieve cookies.txt")
    else:
        print("\n⚠️ Could not trigger the GitHub Action.")
