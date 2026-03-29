import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("HEX_API_KEY", "").strip()
project_id = os.environ.get("HEX_PROJECT_ID", "").strip()

def test_hex():
    print(f"Testing Hex API credentials from .env...")
    print(f"- Project ID: {project_id}")
    print(f"- API Key format check: {api_key[:10] if api_key else 'Missing!'}...")

    if not api_key or not project_id:
        print("ERROR: Missing API Key or Project ID in .env")
        return

    url = f"https://app.hex.tech/api/v1/projects/{project_id}/runs"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Sample basic sprint status inputs
    data = json.dumps({
        "updatePublishedResults": False,
        "useCachedSqlResults": False,
        "inputParams": {
            "sprint_name": "Local Diagnostic Integration Test",
            "done_count": 20
        }
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        print("Sending POST request to Hex API...")
        with urllib.request.urlopen(req) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            print("\n✅ SUCCESS: Project run triggered!")
            print(f"  Run ID: {resp_data.get('runId')}")
            print(f"  Embed URL: {resp_data.get('runUrl')}")
    except urllib.error.HTTPError as e:
        print(f"\n❌ ERROR: Hex API returned HTTP {e.code} - {e.reason}")
        try:
            print(f"  Body: {e.read().decode('utf-8')}")
        except:
            pass
        if e.code in [401, 403]:
            print("\n❗ Auth Issue: Double check that the API Key is a valid hxtw_ or hxtp_ token.")
            print("Note: The Hex API requires the 'Team' or 'Enterprise' paid billing plan.")

if __name__ == "__main__":
    test_hex()
