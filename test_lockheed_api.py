
import requests
import json

url = "https://lockheedmartin.eightfold.ai/api/pcsx/search"

params = {
    "domain": "lockheedmartin.com",
    "query": "",
    "location": "",
    "start": 0,
    "sort_by": "timestamp"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=30
)

print("HTTP status:", response.status_code)
response.raise_for_status()

data = response.json()

# Extract job listings
positions = data.get("data", {}).get("positions", [])

print("\n========== API REPORT ==========")

print("Jobs returned:", len(positions))

print("\nTop-level data fields:")
print(data.get("data", {}).keys())

print("\nMetadata:")
print(json.dumps(data.get("metadata"), indent=2))

if positions:
    print("\nFields available in each job:")
    print(positions[0].keys())

    print("\nFirst five job titles:")
    for job in positions[:5]:
        print("-", job.get("name"))

    print("\nFirst job's complete information:")
    print(json.dumps(positions[0], indent=2)[:4000])

# Save raw data
with open("lockheed_raw_response.json", "w") as f:
    json.dump(data, f, indent=4)

print("\nRaw data saved.")
