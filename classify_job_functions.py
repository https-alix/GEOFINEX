
import pandas as pd
import re
from pathlib import Path

# ==================================================
# 1. LOAD DATA
# ==================================================

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
print("Total vacancies:", len(df))


# ==================================================
# 2. DEFINE OCCUPATIONAL CLASSIFICATION RULES
# ==================================================

# Rules are checked in order.
# More specialised categories come first to reduce
# incorrect assignments.

RULES = [

    (
        "Early Careers & Internships",
        r"\bcollege student\b|\bintern\b|\bco-op\b"
        r"|\bsummer student\b|\bgraduate trainee\b"
    ),

    (
        "Security & Physical Protection",
        r"\bsecurity rep\b|\bsecurity representative\b"
        r"|\bsecurity manager\b|\bsecurity specialist\b"
        r"|\bphysical security\b|\bsecurity officer\b"
    ),

    (
        "Contracts & Commercial",
        r"\bcontracts management\b|\bcontract management\b"
        r"|\bcontract administrator\b|\bcontract specialist\b"
        r"|\bcontract negotiation\b|\bcontracts analyst\b"
        r"|\bsubcontract administration\b"
    ),

    (
        "Technical Maintenance & Field Service",
        r"\bfield and service mech\b|\bmaintenance\b"
        r"|\bmechanic\b|\bavionics technician\b"
        r"|\belectronics tech\b|\btechnician\b"
        r"|\bflight completion\b"
    ),

    (
        "Training & Development",
        r"\btrainer\b|\binstructor\b|\btraining specialist\b"
    ),

    (
        "Property & Asset Management",
        r"\bproperty analyst\b|\bproperty management\b"
        r"|\basset management\b"
    ),

    (
        "Communications",
        r"\bcommunications rep\b|\bcommunications specialist\b"
        r"|\bpublic relations\b|\bmedia relations\b"
    ),

    (
        "Programme Planning & Scheduling",
        r"\bintegrated program planner\b"
        r"|\bintegrated programme planner\b"
        r"|\bprogram planner\b|\bprogramme planner\b"
        r"|\bscheduling analyst\b"
    ),


    (
        "Cybersecurity",
        r"\bcyber\b|\binformation security\b|\bsecurity engineer\b"
        r"|\bsecurity analyst\b|\binfosec\b"
    ),

    (
        "Software & IT",
        r"\bsoftware\b|\bcomputer\b|\bnetwork engineer\b"
        r"|\bsystems administrator\b|\bsystem administrator\b"
        r"|\bIT support\b|\bIT analyst\b|\bIT specialist\b"
        r"|\binformation systems\b|\bcloud\b|\bDevSec\b"
        r"|\bdata analyst\b|\bdata scientist\b"
        r"|\bdatabase\b|\bdeveloper\b|\bprogrammer\b"
        r"|\bsystems administration\b|\bERP business analyst\b"
        r"|\binfo systems analyst\b"
    ),

    (
        "Quality & Testing",
        r"\bquality\b|\binspector\b|\binspection\b"
        r"|\btest engineer\b|\btest technician\b"
        r"|\bflight test\b|\btesting\b"
    ),

    (
        "Manufacturing & Production",
        r"\bmanufactur\w*\b|\bfabricator\b|\bmachinist\b"
        r"|\bproduction\b|\bassembly\b|\bassembler\b"
        r"|\bwelder\b|\bmaintenance technician\b"
        r"|\bproduction technician\b|\bCNC\b"
    ),

    (
        "Supply Chain & Procurement",
        r"\bsupply chain\b|\bprocurement\b|\bbuyer\b"
        r"|\bpurchasing\b|\bsourcing\b|\bsubcontract\b"
        r"|\bsupplier\b|\binventory\b|\bmaterials management\b"
    ),

    (
        "Programme & Project Management",
        r"\bprogram manager\b|\bprogramme manager\b"
        r"|\bproject manager\b|\bproject management\b"
        r"|\bprogram management\b|\bprogramme management\b"
        r"|\bprogramme control\b"
    ),

    (
        "Business Development & Strategy",
        r"\bbusiness development\b|\bstrategy\b"
        r"|\bstrategic\b|\bpartnership\b"
        r"|\bmarket development\b|\bcapture manager\b"
    ),

    (
        "Finance & Accounting",
        r"\bfinance\b|\bfinancial\b|\baccountant\b"
        r"|\baccounting\b|\btreasury\b|\baudit\b"
    ),

    (
        "Human Resources",
        r"\bHR\b|\bhuman resources\b|\brecruiter\b"
        r"|\btalent acquisition\b|\bpeople operations\b"
    ),

    (
        "Legal & Compliance",
        r"\blegal\b|\battorney\b|\bcounsel\b"
        r"|\bcompliance\b|\bcontracts specialist\b"
    ),

    (
        "Engineering",
        r"\bengineer\b|\bengineering\b|\bengineering technician\b"
        r"|\bsystems architect\b|\btechnical fellow\b"
    ),

    (
        "Logistics & Operations",
        r"\blogistics\b|\bwarehouse\b|\bshipping\b"
        r"|\bdistribution\b|\boperations\b|\bfield service\b"
        r"|\bfield support\b|\bdispatcher\b"
    ),

    (
        "Administration & Support",
        r"\badministrative\b|\badministrator\b"
        r"|\bexecutive assistant\b|\bcoordinator\b"
        r"|\breceptionist\b|\boffice assistant\b"
        r"|\bclerical\b"
    ),

]


# ==================================================
# 3. CLASSIFY EACH JOB TITLE
# ==================================================

def classify_job(title):

    if pd.isna(title):
        return "Other / Unclassified", "No job title"

    title = str(title).strip()

    for category, pattern in RULES:

        if re.search(pattern, title, re.IGNORECASE):
            return category, pattern

    return "Other / Unclassified", "No matching rule"


classification_results = df["name"].apply(classify_job)

df["job_function"] = classification_results.apply(
    lambda result: result[0]
)

df["classification_rule"] = classification_results.apply(
    lambda result: result[1]
)


# ==================================================
# 4. OVERALL CLASSIFICATION RESULTS
# ==================================================

print("\n========== JOB FUNCTION BREAKDOWN ==========")

function_counts = df["job_function"].value_counts()

function_summary = pd.DataFrame({
    "vacancies": function_counts,
    "percentage": (
        function_counts / len(df) * 100
    ).round(2)
})

print(function_summary.to_string())


classified_count = (
    df["job_function"] != "Other / Unclassified"
).sum()

unclassified_count = len(df) - classified_count

print("\n========== CLASSIFICATION COVERAGE ==========")

print("Classified:", classified_count)
print("Unclassified:", unclassified_count)

print(
    "Classification rate:",
    round(classified_count / len(df) * 100, 2),
    "%"
)


# ==================================================
# 5. JOB FUNCTIONS BY DEPARTMENT
# ==================================================

print("\n========== JOB FUNCTIONS BY DEPARTMENT ==========")

department_function = pd.crosstab(
    df["department"],
    df["job_function"]
)

department_function["TOTAL"] = department_function.sum(axis=1)

department_function = department_function.sort_values(
    "TOTAL",
    ascending=False
)

print(department_function.head(20).to_string())


# ==================================================
# 6. MOST COMMON JOB TITLES
# ==================================================

print("\n========== TOP 25 JOB TITLES ==========")

print(
    df["name"]
    .value_counts()
    .head(25)
    .to_string()
)


# ==================================================
# 7. REVIEW UNCLASSIFIED TITLES
# ==================================================

print("\n========== UNCLASSIFIED JOB TITLES ==========")

unclassified = df[
    df["job_function"] == "Other / Unclassified"
]

print(
    unclassified["name"]
    .value_counts()
    .head(50)
    .to_string()
)


# ==================================================
# 8. SAVE OUTPUTS
# ==================================================

classified_file = OUTPUT_FOLDER / "lockheed_jobs_classified.csv"

summary_file = OUTPUT_FOLDER / "job_function_summary.csv"

department_file = OUTPUT_FOLDER / "job_functions_by_department.csv"

unclassified_file = OUTPUT_FOLDER / "unclassified_job_titles.csv"

df.to_csv(classified_file, index=False)

function_summary.to_csv(summary_file)

department_function.to_csv(department_file)

unclassified.to_csv(unclassified_file, index=False)


print("\n========== FILES SAVED ==========")

print("Classified dataset:", classified_file)
print("Function summary:", summary_file)
print("Department breakdown:", department_file)
print("Unclassified jobs:", unclassified_file)

print("\nClassification analysis complete.")
