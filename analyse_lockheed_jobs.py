
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# 1. FIND THE LATEST DATASET
# ==========================================

PROJECT_FOLDER = Path(__file__).resolve().parent
RAW_FOLDER = PROJECT_FOLDER / "data" / "raw"
PROCESSED_FOLDER = PROJECT_FOLDER / "data" / "processed"
OUTPUT_FOLDER = PROJECT_FOLDER / "outputs"

PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

files = sorted(RAW_FOLDER.glob("lockheed_jobs_*.csv"))

if not files:
    raise FileNotFoundError("No Lockheed CSV files found.")

latest_file = files[-1]
df = pd.read_csv(latest_file)

print("Loaded:", latest_file.name)
print("Original records:", len(df))


# ==========================================
# 2. CLEAN LIST FIELDS
# ==========================================

def parse_list(value):
    if pd.isna(value):
        return []

    try:
        result = json.loads(value)

        if isinstance(result, list):
            return result

        return [result]

    except (ValueError, TypeError):
        return [str(value)]


df["location_list"] = df["locations"].apply(parse_list)

df["experience_list"] = df[
    "efcustomTextLevelofexperience"
].apply(parse_list)

# Use the first listed location as the primary location.
df["primary_location"] = df["location_list"].apply(
    lambda x: x[0] if x else "Unknown"
)

# Extract the experience classification.
df["experience_level"] = df["experience_list"].apply(
    lambda x: x[0] if x else "Unknown"
)


# ==========================================
# 3. CONVERT POSTING DATES
# ==========================================

df["posted_date_utc"] = pd.to_datetime(
    df["postedTs"],
    unit="s",
    utc=True,
    errors="coerce"
)

df["creation_date_utc"] = pd.to_datetime(
    df["creationTs"],
    unit="s",
    utc=True,
    errors="coerce"
)


# ==========================================
# 4. DATA QUALITY CHECKS
# ==========================================

print("\n========== DATA QUALITY ==========")

print("Unique job IDs:", df["id"].nunique())
print("Duplicate job IDs:", df["id"].duplicated().sum())

print("\nMissing values:")
print(df.isna().sum().sort_values(ascending=False).head(10))

print("\nDate range:")
print("Earliest:", df["posted_date_utc"].min())
print("Latest:", df["posted_date_utc"].max())


# ==========================================
# 5. DEPARTMENT ANALYSIS
# ==========================================

department_counts = df["department"].value_counts()

print("\n========== TOP DEPARTMENTS ==========")
print(department_counts.head(15))

plt.figure(figsize=(12, 7))

department_counts.head(15).sort_values().plot(
    kind="barh"
)

plt.title("Lockheed Martin: Vacancies by Department")
plt.xlabel("Number of advertised vacancies")
plt.ylabel("Department")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "department_analysis.png",
    dpi=200
)

plt.close()


# ==========================================
# 6. EXPERIENCE ANALYSIS
# ==========================================

experience_counts = df["experience_level"].value_counts()

print("\n========== EXPERIENCE LEVELS ==========")
print(experience_counts)

plt.figure(figsize=(10, 6))

experience_counts.plot(
    kind="bar"
)

plt.title("Lockheed Martin: Vacancies by Experience Level")
plt.xlabel("Experience level")
plt.ylabel("Number of vacancies")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "experience_analysis.png",
    dpi=200
)

plt.close()


# ==========================================
# 7. LOCATION ANALYSIS
# ==========================================

location_counts = df.explode(
    "location_list"
)["location_list"].value_counts()

print("\n========== TOP LOCATIONS ==========")
print(location_counts.head(15))

plt.figure(figsize=(12, 7))

location_counts.head(15).sort_values().plot(
    kind="barh"
)

plt.title("Lockheed Martin: Vacancies by Advertised Location")
plt.xlabel("Number of listings")
plt.ylabel("Location")
plt.tight_layout()

plt.savefig(
    OUTPUT_FOLDER / "location_analysis.png",
    dpi=200
)

plt.close()


# ==========================================
# 8. SAVE CLEANED DATASET
# ==========================================

cleaned_file = (
    PROCESSED_FOLDER / "lockheed_jobs_clean.csv"
)

# Remove helper list columns before exporting.
export_df = df.drop(
    columns=["location_list", "experience_list"]
)

export_df.to_csv(
    cleaned_file,
    index=False
)


# ==========================================
# 9. FINAL SUMMARY
# ==========================================

print("\n====================================")
print("ANALYSIS COMPLETE")
print("====================================")

print("Jobs analysed:", len(df))
print("Unique IDs:", df["id"].nunique())

print("\nCleaned dataset:")
print(cleaned_file)

print("\nCharts saved in:")
print(OUTPUT_FOLDER)

print("\n====================================")
