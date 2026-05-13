# 02_create_silver.py
import pandas as pd
from sqlalchemy import create_engine, text
import sys

sys.path.insert(0, r"D:\projects\healthcare\rwe")
from config import CONNECTION_STRING

print("=" * 60)
print("SILVER LAYER — CODE MAPPING & COHORT DEFINITION")
print("=" * 60)

engine = create_engine(CONNECTION_STRING)

def run_query(engine, sql):
    """Helper: run any SQL and return a DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── STEP A: Create SNOMED to ICD-10 Mapping Table ─────────────
print("\nCreating SNOMED → ICD-10 mapping table...")

mapping_data = [
    {"snomed_code": "57724001000119103", "snomed_desc": "Myasthenia gravis (disorder)",           "icd10_code": "G70.00",  "condition_name": "Myasthenia Gravis",     "mapping_source": "NLM"},
    {"snomed_code": "91637004",          "snomed_desc": "Myasthenia gravis without exacerbation", "icd10_code": "G70.00",  "condition_name": "Myasthenia Gravis",     "mapping_source": "NLM"},
    {"snomed_code": "57636002",          "snomed_desc": "Myasthenia gravis with exacerbation",    "icd10_code": "G70.01",  "condition_name": "Myasthenia Gravis",     "mapping_source": "NLM"},
    {"snomed_code": "44054006",          "snomed_desc": "Diabetes mellitus type 2",               "icd10_code": "E11.9",   "condition_name": "Type 2 Diabetes",       "mapping_source": "NLM"},
    {"snomed_code": "73211009",          "snomed_desc": "Diabetes mellitus (disorder)",           "icd10_code": "E11",     "condition_name": "Type 2 Diabetes",       "mapping_source": "NLM"},
    {"snomed_code": "38341003",          "snomed_desc": "Hypertensive disorder",                  "icd10_code": "I10",     "condition_name": "Hypertension",          "mapping_source": "NLM"},
    {"snomed_code": "53741008",          "snomed_desc": "Coronary arteriosclerosis",              "icd10_code": "I25.10",  "condition_name": "Coronary Artery Disease","mapping_source": "NLM"},
    {"snomed_code": "84114007",          "snomed_desc": "Heart failure (disorder)",               "icd10_code": "I50.9",   "condition_name": "Heart Failure",         "mapping_source": "NLM"},
    {"snomed_code": "195967001",         "snomed_desc": "Asthma (disorder)",                      "icd10_code": "J45.909", "condition_name": "Asthma",                "mapping_source": "NLM"},
    {"snomed_code": "13645005",          "snomed_desc": "Chronic obstructive lung disease",       "icd10_code": "J44.1",   "condition_name": "COPD",                  "mapping_source": "NLM"},
    {"snomed_code": "709044004",         "snomed_desc": "Chronic kidney disease",                 "icd10_code": "N18.9",   "condition_name": "Chronic Kidney Disease", "mapping_source": "NLM"},
    {"snomed_code": "230690007",         "snomed_desc": "Cerebrovascular accident",               "icd10_code": "I63.9",   "condition_name": "Stroke",                "mapping_source": "NLM"},
    {"snomed_code": "40930008",          "snomed_desc": "Hypothyroidism (disorder)",              "icd10_code": "E03.9",   "condition_name": "Hypothyroidism",        "mapping_source": "NLM"},
    {"snomed_code": "363406005",         "snomed_desc": "Malignant neoplasm of colon",            "icd10_code": "C18.9",   "condition_name": "Colon Cancer",          "mapping_source": "NLM"},
    {"snomed_code": "19829001",          "snomed_desc": "Disorder of lung",                       "icd10_code": "J98.4",   "condition_name": "Lung Disorder",         "mapping_source": "NLM"},
]

mapping_df = pd.DataFrame(mapping_data)
mapping_df.to_sql("code_mapping", engine, schema="silver", if_exists="replace", index=False)
print(f"✅ Mapping table created: {len(mapping_df)} mappings")

# ── STEP B: Check top conditions ──────────────────────────────
print("\nChecking top conditions in your data...")
existing = run_query(engine, """
    SELECT "CODE", "DESCRIPTION", COUNT(*) as freq
    FROM bronze.raw_conditions
    GROUP BY "CODE", "DESCRIPTION"
    ORDER BY freq DESC
    LIMIT 20
""")
print(existing.to_string(index=False))
existing.to_csv(r"D:\projects\healthcare\rwe\data\existing_condition_codes.csv", index=False)

# ── STEP C: Search for MG patients ────────────────────────────
print("\n" + "="*40)
print("Searching for Myasthenia Gravis patients...")

mg_by_desc = run_query(engine, """
    SELECT "PATIENT", "CODE", "DESCRIPTION", "START", "STOP", "ENCOUNTER"
    FROM bronze.raw_conditions
    WHERE LOWER("DESCRIPTION") LIKE '%myasthenia%'
""")

mg_by_code = run_query(engine, """
    SELECT "PATIENT", "CODE", "DESCRIPTION", "START", "STOP", "ENCOUNTER"
    FROM bronze.raw_conditions
    WHERE "CODE" IN ('57724001000119103','91637004','57636002')
""")

print(f"MG by description: {len(mg_by_desc)} records")
print(f"MG by SNOMED code: {len(mg_by_code)} records")

mg_combined = pd.concat([mg_by_desc, mg_by_code]).drop_duplicates()
print(f"Total MG records:  {len(mg_combined)}")

# ── STEP D: Proxy if MG not found ─────────────────────────────
if len(mg_combined) == 0:
    print("\n⚠️  No MG patients — expected for Synthea.")
    print("   Using Type 2 Diabetes as proxy.\n")

    USE_PROXY     = True
    DISEASE_NAME  = "Type 2 Diabetes (Proxy for MG Pipeline Demo)"
    DISEASE_SHORT = "diabetes_proxy"

    study_conditions = run_query(engine, """
        SELECT "PATIENT", "CODE", "DESCRIPTION", "START", "STOP", "ENCOUNTER"
        FROM bronze.raw_conditions
        WHERE "CODE" IN ('44054006','73211009')
           OR LOWER("DESCRIPTION") LIKE '%type 2 diabetes%'
           OR LOWER("DESCRIPTION") LIKE '%diabetes mellitus type 2%'
    """)
    print(f"✅ Proxy records found: {len(study_conditions):,}")
else:
    USE_PROXY     = False
    DISEASE_NAME  = "Myasthenia Gravis"
    DISEASE_SHORT = "mg"
    study_conditions = mg_combined
    print(f"✅ MG records: {len(study_conditions):,}")

# Save config
with open(r"D:\projects\healthcare\rwe\data\disease_config.txt", "w") as f:
    f.write(f"DISEASE_NAME={DISEASE_NAME}\n")
    f.write(f"DISEASE_SHORT={DISEASE_SHORT}\n")
    f.write(f"USE_PROXY={USE_PROXY}\n")

# ── STEP E: Phenotyping — 2+ encounters rule ───────────────────
print(f"\nApplying phenotyping algorithm (≥2 coded encounters)...")

# Uppercase all column names for consistency
study_conditions.columns = [c.upper() for c in study_conditions.columns]

encounter_counts = study_conditions.groupby('PATIENT').agg(
    n_encounters = ('ENCOUNTER', 'nunique'),
    index_date   = ('START',    'min'),
    last_date    = ('START',    'max'),
    primary_code = ('CODE',     'first'),
    primary_desc = ('DESCRIPTION', 'first')
).reset_index()

cohort_patients = encounter_counts[encounter_counts['n_encounters'] >= 2].copy()

print(f"Patients before 2+ rule: {len(encounter_counts):,}")
print(f"Patients after  2+ rule: {len(cohort_patients):,}")
print(f"Excluded:                {len(encounter_counts) - len(cohort_patients):,}")

# ── STEP F: Check patient column names then join ───────────────
print("\nChecking patient table columns...")
pat_cols = run_query(engine, """
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'bronze' AND table_name = 'raw_patients'
    ORDER BY ordinal_position
""")
print(pat_cols['column_name'].tolist())

patients = run_query(engine, 'SELECT * FROM bronze.raw_patients LIMIT 1')
print(f"Patient columns: {list(patients.columns)}")

# Load full patients
patients = run_query(engine, 'SELECT * FROM bronze.raw_patients')

# Find the ID column (could be 'Id', 'ID', 'id', 'PATIENT')
id_col = [c for c in patients.columns if c.upper() == 'ID'][0]
bd_col = [c for c in patients.columns if 'BIRTH' in c.upper()][0]
dd_col = [c for c in patients.columns if 'DEATH' in c.upper()][0]
gd_col = [c for c in patients.columns if 'GENDER' in c.upper() or 'SEX' in c.upper()][0]
rc_col = [c for c in patients.columns if 'RACE' in c.upper()][0]

print(f"\nUsing columns: id={id_col}, birthdate={bd_col}, deathdate={dd_col}, gender={gd_col}, race={rc_col}")

# ── STEP G: Merge and compute age ─────────────────────────────
cohort = cohort_patients.merge(patients, left_on='PATIENT', right_on=id_col, how='left')

cohort['index_date'] = pd.to_datetime(cohort['index_date'])
cohort[bd_col]       = pd.to_datetime(cohort[bd_col])
cohort['age_at_index'] = ((cohort['index_date'] - cohort[bd_col]).dt.days / 365.25).round(1)

cohort['age_group'] = pd.cut(
    cohort['age_at_index'],
    bins=[0, 18, 40, 60, 75, 150],
    labels=['<18', '18-40', '40-60', '60-75', '75+']
)

cohort['is_deceased'] = cohort[dd_col].notna().astype(int)

# ── STEP H: Save to Silver ─────────────────────────────────────
cohort.to_sql(f"{DISEASE_SHORT}_cohort", engine, schema="silver",
              if_exists="replace", index=False)

print(f"\n✅ Silver cohort saved: silver.{DISEASE_SHORT}_cohort")
print(f"   Total patients: {len(cohort):,}")

print("\n── DEMOGRAPHICS PREVIEW ──")
print(f"Median age: {cohort['age_at_index'].median():.1f} years")
print(f"Female:     {(cohort[gd_col]=='F').mean()*100:.1f}%")
print(f"Deceased:   {cohort['is_deceased'].mean()*100:.1f}%")
print(f"\nAge groups:\n{cohort['age_group'].value_counts().sort_index()}")
print(f"\nRace:\n{cohort[rc_col].value_counts()}")

print("\n✅ SILVER LAYER COMPLETE!")