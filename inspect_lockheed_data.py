
import json

# Read the response we already downloaded
with open("lockheed_raw_response.json", "r") as file:
    data = json.load(file)

job_data = data["data"]

print("========== LOCKHEED MARTIN DATA ==========")

print("\nTotal matching jobs:")
print(job_data.get("count"))

print("\nJobs in this downloaded batch:")
print(len(job_data.get("positions", [])))

print("\nResults metadata:")
print(json.dumps(job_data.get("resultsMetaData"), indent=2))

print("\nSorting method:")
print(job_data.get("sortBy"))

print("\n==========================================")

positions = job_data.get("positions", [])

first_page_ids = [job["id"] for job in positions]

print("\nFirst page verification:")
print("First job:", positions[0]["name"])
print("First job ID:", positions[0]["id"])
print("Last job:", positions[-1]["name"])
print("Last job ID:", positions[-1]["id"])

print("\nDoes the second page's first job appear on page one?")
print(996478132567 in first_page_ids)