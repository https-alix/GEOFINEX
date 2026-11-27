
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_URL = "https://lockheedmartin.eightfold.ai/api/pcsx/search"

PARAMS = {
    "domain": "lockheedmartin.com",
    "query": "",
    "location": "",
    "sort_by": "timestamp"
}

BATCH_SIZE = 10

# PILOT SETTING: collect only 3 pages (30 jobs).
# Later, change this to None to collect all available pages.
MAX_PAGES = None

# Wait between successful requests.
REQUEST_DELAY = 5

# Maximum number of retries after a rate-limit response.
MAX_RETRIES = 2

OUTPUT_FOLDER = Path("data/raw")


# ==========================================
# 2. SET UP THE COLLECTION
# ==========================================

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

session = requests.Session()

collection_time = datetime.now(timezone.utc)
collection_timestamp = collection_time.isoformat()

file_timestamp = collection_time.strftime("%Y%m%d_%H%M%S")

csv_path = OUTPUT_FOLDER / f"lockheed_jobs_{file_timestamp}.csv"
json_path = OUTPUT_FOLDER / f"lockheed_jobs_{file_timestamp}.json"

all_jobs = []
raw_pages = []
seen_job_ids = set()

start = 0
page_number = 0
total_jobs = None


# ==========================================
# 3. DOWNLOAD JOB LISTINGS
# ==========================================

print("Starting Lockheed Martin job extraction...")
print("Collection time:", collection_timestamp)
print("Pilot page limit:", MAX_PAGES)
print("------------------------------------------")

while total_jobs is None or start < total_jobs:

    if MAX_PAGES is not None and page_number >= MAX_PAGES:
        print("Reached pilot page limit.")
        break

    params = PARAMS.copy()
    params["start"] = start

    print(f"\nRequesting page {page_number + 1}")
    print("Starting position:", start)

    # Make the request, with limited handling of rate limits.
    response = None

    for attempt in range(MAX_RETRIES + 1):

        response = session.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        if response.status_code == 429:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    "Rate limit persisted after retries. "
                    "Stopping the extraction safely."
                )

            retry_after = response.headers.get("Retry-After")

            try:
                wait_time = float(retry_after)
            except (TypeError, ValueError):
                wait_time = 60

            print(
                f"Rate limited. Waiting {wait_time} seconds "
                "before retrying."
            )
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        break

    result = response.json()
    job_data = result["data"]

    positions = job_data.get("positions", [])
    total_jobs = job_data.get("count", 0)

    print("Total matching jobs:", total_jobs)
    print("Jobs returned on this page:", len(positions))

    # Preserve the original response for later reference.
    raw_pages.append({
        "start": start,
        "response": result
    })

    if not positions:
        print("No more jobs returned. Ending extraction.")
        break

    # Add each job, skipping duplicate IDs.
    new_jobs = 0

    for job in positions:

        job_id = job.get("id")

        if not job_id or job_id in seen_job_ids:
            continue

        seen_job_ids.add(job_id)

        job["collection_timestamp_utc"] = collection_timestamp
        job["page_start"] = start

        all_jobs.append(job)
        new_jobs += 1

    print("New unique jobs collected:", new_jobs)
    print("Total unique jobs collected:", len(all_jobs))

    page_number += 1

    # Move forward by the number of records actually returned.
    start += len(positions)

    if len(positions) < BATCH_SIZE:
        print("Last page appears to be reached.")
        break

    time.sleep(REQUEST_DELAY)


# ==========================================
# 4. SAVE THE CSV FILE
# ==========================================

if not all_jobs:
    raise RuntimeError("No jobs were collected. No CSV was created.")

# Build a CSV containing every field returned by the API.
fieldnames = set()

for job in all_jobs:
    fieldnames.update(job.keys())

fieldnames = sorted(fieldnames)

with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
        extrasaction="ignore"
    )

    writer.writeheader()

    for job in all_jobs:

        clean_job = {}

        for key, value in job.items():

            if isinstance(value, (dict, list)):
                clean_job[key] = json.dumps(value, ensure_ascii=False)
            else:
                clean_job[key] = value

        writer.writerow(clean_job)
print("\nCSV file successfully created:", csv_path.resolve())
print("Does the file exist?", csv_path.exists())

# ==========================================
# 5. SAVE THE RAW JSON
# ==========================================

raw_output = {
    "collection_timestamp_utc": collection_timestamp,
    "total_jobs_reported": total_jobs,
    "unique_jobs_collected": len(all_jobs),
    "pages_collected": page_number,
    "pages": raw_pages
}

with open(json_path, "w", encoding="utf-8") as file:
    json.dump(raw_output, file, indent=2, ensure_ascii=False)


# ==========================================
# 6. COLLECTION SUMMARY
# ==========================================

print("\n==========================================")
print("EXTRACTION COMPLETE")
print("==========================================")

print("Pages collected:", page_number)
print("Unique jobs collected:", len(all_jobs))
print("Total jobs reported by API:", total_jobs)

print("\nCSV saved to:")
print(csv_path)

print("\nRaw JSON saved to:")
print(json_path)

print("\n==========================================")
