
import pandas as pd
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
RAW = PROJECT / "data" / "raw"

files = sorted(RAW.glob("lockheed_jobs_*.csv"))
df = pd.read_csv(files[-1])

print("\n========== FIELD COVERAGE ==========\n")

fields = [
    "name",
    "department",
    "locations",
    "efcustomTextCustpayrange",
    "efcustomTextCustpreferredsalaryV2",
    "efcustomTextLevelofexperience",
    "postedTs",
    "positionUrl"
]

for field in fields:
    if field not in df.columns:
        continue

    populated = df[field].notna() & (
        df[field].astype(str).str.strip() != ""
    )

    print(f"{field}: {populated.sum()} / {len(df)} populated")

print("\n========== SALARY EXAMPLES ==========\n")

print(
    df.loc[
        df["efcustomTextCustpreferredsalaryV2"].notna(),
        ["name", "department", "locations",
         "efcustomTextCustpreferredsalaryV2"]
    ].head(15).to_string(index=False)
)

print("\n========== JOB TITLE EXAMPLES ==========\n")

for title in df["name"].dropna().sample(
    min(30, df["name"].notna().sum()),
    random_state=42
):
    print("-", title)

print("\n====================================")

