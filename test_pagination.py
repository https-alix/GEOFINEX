
import requests

url = "https://lockheedmartin.eightfold.ai/api/pcsx/search"

params = {
    "domain": "lockheedmartin.com",
    "query": "",
    "location": "",
    "start": 10,
    "sort_by": "timestamp"
}

response = requests.get(url, params=params, timeout=30)

print("HTTP status:", response.status_code)

if response.status_code == 200:
    data = response.json()["data"]
    positions = data["positions"]

    print("Total jobs:", data["count"])
    print("Jobs returned:", len(positions))

    print("\nFirst job on this page:")
    print(positions[0]["name"])
    print("Job ID:", positions[0]["id"])

else:
    print("Request unsuccessful.")
    print(response.text[:500])
