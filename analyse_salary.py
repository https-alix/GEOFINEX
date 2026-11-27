
import pandas as pd
import re
import ast
from pathlib import Path

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

PROJECT_FOLDER = Path(__file__).resolve().parent
RAW_FOLDER = PROJECT_FOLDER / "data" / "raw"
OUTPUT_FOLDER = PROJECT_FOLDER / "data" / "processed"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

files = sorted(RAW_FOLDER.glob("lockheed_jobs_*.csv"))

if not files:
    raise FileNotFoundError("No Lockheed Martin CSV files found.")

csv_file = files[-1]
df = pd.read_csv(csv_file)

print("Dataset:", csv_file.name)
print("Total jobs:", len(df))


# --------------------------------------------------
# 2. PARSE SALARY VALUES
# --------------------------------------------------

def extract_salary(value):

    result = {
        "salary_text": None,
        "currency": None,
        "salary_min": None,
        "salary_max": None,
        "salary_midpoint": None,
        "salary_type": "missing"
    }

    if pd.isna(value):
        return pd.Series(result)

    # Convert the stored list into a Python list
    try:
        parsed = ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        parsed = str(value)

    if isinstance(parsed, list):
        if len(parsed) == 0:
            return pd.Series(result)
        text = " ".join(str(item) for item in parsed)
    else:
        text = str(parsed)

    text = text.strip()

    if not text:
        return pd.Series(result)

    result["salary_text"] = text

    # Recognise common currency symbols and codes
    currency_patterns = [
        (r"NZ\$|NZD", "NZD"),
        (r"C\$|CAD", "CAD"),
        (r"A\$|AUD", "AUD"),
        (r"US\$|USD", "USD"),
        (r"£|GBP", "GBP"),
        (r"€|EUR", "EUR"),
        (r"\bAED\b", "AED"),
        (r"\$", "USD")
    ]

    for pattern, currency in currency_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result["currency"] = currency
            break

    # Extract numerical amounts
    amounts = re.findall(
        r"\d[\d,]*(?:\.\d+)?",
        text
    )

    if len(amounts) >= 2:

        minimum = float(amounts[0].replace(",", ""))
        maximum = float(amounts[1].replace(",", ""))

        result["salary_min"] = minimum
        result["salary_max"] = maximum
        result["salary_midpoint"] = (minimum + maximum) / 2
        result["salary_type"] = "range"

    elif len(amounts) == 1:

        amount = float(amounts[0].replace(",", ""))

        result["salary_min"] = amount
        result["salary_max"] = amount
        result["salary_midpoint"] = amount
        result["salary_type"] = "single"

    else:
        result["salary_type"] = "qualitative"

    return pd.Series(result)


salary_results = df[
    "efcustomTextCustpreferredsalaryV2"
].apply(extract_salary)

df = pd.concat([df, salary_results], axis=1)

# Inspect potentially anomalous salary values

print("\n========== SALARY DATA QUALITY CHECK ==========")

salary_column = "efcustomTextCustpreferredsalaryV2"

suspicious = df[
    (df["salary_midpoint"].notna()) &
    (df["salary_min"] < 1000)
]

print("Number of suspicious entries:", len(suspicious))

for _, row in suspicious.iterrows():
    print("\nJob:", row["name"])
    print("Department:", row["department"])
    print("Original salary:", row[salary_column])
    print("Parsed currency:", row["currency"])
    print("Parsed minimum:", row["salary_min"])
    print("Parsed maximum:", row["salary_max"])


# Check numerical entries with no recognised currency
unknown_currency = df[
    (df["salary_midpoint"].notna()) &
    (df["currency"].isna())
]

print("\n========== UNKNOWN CURRENCY ENTRIES ==========")

for _, row in unknown_currency.iterrows():
    print(row["name"], "|", row[salary_column])



# --------------------------------------------------
# 3. OVERALL COVERAGE
# --------------------------------------------------

print("\n========== SALARY COVERAGE ==========")

print(df["salary_type"].value_counts().to_string())

print(
    "\nJobs with numerical salary information:",
    df["salary_midpoint"].notna().sum()
)

print(
    "Jobs with qualitative salary information:",
    (df["salary_type"] == "qualitative").sum()
)

print(
    "Jobs with no salary information:",
    (df["salary_type"] == "missing").sum()
)

print("\n========== CURRENCY BREAKDOWN ==========")

print(
    df[df["salary_midpoint"].notna()]
    ["currency"]
    .value_counts(dropna=False)
    .to_string()
)


# --------------------------------------------------
# 4. SALARY BY CURRENCY
# --------------------------------------------------

print("\n========== SALARY STATISTICS BY CURRENCY ==========")

salary_by_currency = (
    df[df["salary_midpoint"].notna()]
    .groupby("currency")
    .agg(
        vacancies=("salary_midpoint", "count"),
        average_salary=("salary_midpoint", "mean"),
        median_salary=("salary_midpoint", "median"),
        lowest_salary=("salary_min", "min"),
        highest_salary=("salary_max", "max")
    )
    .round(2)
)

print(salary_by_currency.to_string())


# --------------------------------------------------
# 5. SALARY BY DEPARTMENT AND CURRENCY
# --------------------------------------------------

print("\n========== SALARY BY DEPARTMENT AND CURRENCY ==========")

department_salary = (
    df[df["salary_midpoint"].notna()]
    .groupby(["department", "currency"])
    .agg(
        vacancies=("salary_midpoint", "count"),
        median_salary=("salary_midpoint", "median")
    )
    .sort_values("vacancies", ascending=False)
)

print(department_salary.head(25).to_string())


# --------------------------------------------------
# 6. SALARY BY EXPERIENCE AND CURRENCY
# --------------------------------------------------

print("\n========== SALARY BY EXPERIENCE AND CURRENCY ==========")

experience_salary = (
    df[df["salary_midpoint"].notna()]
    .groupby(["efcustomTextLevelofexperience", "currency"])
    .agg(
        vacancies=("salary_midpoint", "count"),
        median_salary=("salary_midpoint", "median")
    )
    .sort_values("vacancies", ascending=False)
)

print(experience_salary.to_string())


# --------------------------------------------------
# 7. SAVE RESULTS
# --------------------------------------------------

output_file = OUTPUT_FOLDER / "lockheed_salary_analysis.csv"

df.to_csv(output_file, index=False)

print("\nAnalysis saved to:", output_file)
