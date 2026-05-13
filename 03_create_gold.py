# 03_create_gold.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import sys

sys.path.insert(0, r"D:\projects\healthcare\rwe")
from config import CONNECTION_STRING

print("=" * 60)
print("GOLD LAYER — PATIENT CHARACTERISATION")
print("=" * 60)

engine = create_engine(CONNECTION_STRING)

def run_query(engine, sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── Load config ────────────────────────────────────────────────
config = {}
with open(r"D:\projects\healthcare\rwe\data\disease_config.txt") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        config[k] = v

DISEASE_SHORT = config["DISEASE_SHORT"]
DISEASE_NAME  = config["DISEASE_NAME"]
print(f"\nDisease: {DISEASE_NAME}")

# ── Load cohort ────────────────────────────────────────────────
cohort = run_query(engine, f'SELECT * FROM silver.{DISEASE_SHORT}_cohort')
print(f"Cohort size: {len(cohort):,} patients")
print(f"Cohort columns: {list(cohort.columns)}")

# ── Load all conditions for CCI ────────────────────────────────
print("\nLoading all conditions...")
all_conditions = run_query(engine,
    'SELECT "PATIENT", "CODE", "DESCRIPTION" FROM bronze.raw_conditions'
)
all_conditions.columns = ['PATIENT', 'CODE', 'DESCRIPTION']
print(f"Total condition records: {len(all_conditions):,}")

# ── Load medications ───────────────────────────────────────────
print("Loading medications...")
med_cols = run_query(engine,
    """SELECT column_name FROM information_schema.columns
       WHERE table_schema='bronze' AND table_name='raw_medications'
       ORDER BY ordinal_position"""
)
print(f"Medication columns: {med_cols['column_name'].tolist()}")

all_medications = run_query(engine,
    'SELECT * FROM bronze.raw_medications LIMIT 1'
)
print(f"Medication sample columns: {list(all_medications.columns)}")

all_medications = run_query(engine,
    'SELECT "PATIENT", "DESCRIPTION" FROM bronze.raw_medications'
)
all_medications.columns = ['PATIENT', 'DESCRIPTION']

# ── Load encounters ────────────────────────────────────────────
print("Loading encounters...")
all_encounters = run_query(engine,
    'SELECT * FROM bronze.raw_encounters LIMIT 1'
)
print(f"Encounter sample columns: {list(all_encounters.columns)}")

# Find the right column names
enc_cols     = list(all_encounters.columns)
pat_enc_col  = [c for c in enc_cols if 'PATIENT' in c.upper()][0]
id_enc_col   = [c for c in enc_cols if c.upper() == 'ID'][0]
class_col    = [c for c in enc_cols if 'CLASS' in c.upper()][0]

all_encounters = run_query(engine,
    f'SELECT "{pat_enc_col}", "{id_enc_col}", "{class_col}" FROM bronze.raw_encounters'
)
all_encounters.columns = ['PATIENT', 'ID', 'ENCOUNTERCLASS']

# ── CHARLSON COMORBIDITY INDEX ─────────────────────────────────
print("\nCalculating Charlson Comorbidity Index...")

cci_conditions = {
    "myocardial_infarction":      {"keywords": ["myocardial infarction", "heart attack"],         "weight": 1},
    "congestive_heart_failure":   {"keywords": ["heart failure", "cardiac failure"],               "weight": 1},
    "peripheral_vascular":        {"keywords": ["peripheral vascular", "peripheral artery"],       "weight": 1},
    "cerebrovascular":            {"keywords": ["stroke", "cerebrovascular", "transient ischemic"],"weight": 1},
    "dementia":                   {"keywords": ["dementia", "alzheimer"],                          "weight": 1},
    "copd":                       {"keywords": ["chronic obstructive", "emphysema", "copd"],       "weight": 1},
    "rheumatologic":              {"keywords": ["rheumatoid", "lupus", "systemic sclerosis"],      "weight": 1},
    "peptic_ulcer":               {"keywords": ["peptic ulcer", "gastric ulcer"],                  "weight": 1},
    "mild_liver":                 {"keywords": ["liver disease", "hepatitis", "cirrhosis"],        "weight": 1},
    "diabetes_uncomplicated":     {"keywords": ["diabetes mellitus type 2", "type 2 diabetes"],    "weight": 1},
    "diabetes_complicated":       {"keywords": ["diabetic nephropathy", "diabetic neuropathy"],    "weight": 2},
    "hemiplegia":                 {"keywords": ["hemiplegia", "hemiparesis", "paraplegia"],        "weight": 2},
    "renal_disease":              {"keywords": ["renal failure", "kidney disease", "dialysis"],    "weight": 2},
    "malignancy":                 {"keywords": ["cancer", "carcinoma", "malignant", "lymphoma"],   "weight": 2},
    "severe_liver":               {"keywords": ["liver failure", "hepatic failure"],               "weight": 3},
    "metastatic_tumor":           {"keywords": ["metastatic", "metastasis"],                       "weight": 6},
    "aids":                       {"keywords": ["hiv", "aids", "immunodeficiency"],                "weight": 6},
}

def compute_cci(patient_id, conditions_df):
    pt_conds = conditions_df[
        conditions_df['PATIENT'] == patient_id
    ]['DESCRIPTION'].str.lower().tolist()

    score = 0
    flags = {}
    for name, info in cci_conditions.items():
        hit = any(
            any(kw in c for kw in info["keywords"])
            for c in pt_conds
        )
        flags[name] = int(hit)
        if hit:
            score += info["weight"]
    flags['cci_score'] = score
    return flags

print("  Computing CCI (may take 1-2 minutes)...")
cci_rows = []
patient_ids = cohort['PATIENT'].tolist()

for i, pid in enumerate(patient_ids):
    row = compute_cci(pid, all_conditions)
    row['PATIENT'] = pid
    cci_rows.append(row)
    if (i + 1) % 100 == 0:
        print(f"  {i+1}/{len(patient_ids)} done...")

cci_df = pd.DataFrame(cci_rows)
print(f"✅ CCI computed for {len(cci_df):,} patients")
print(f"   Median CCI: {cci_df['cci_score'].median()}")
print(f"   Mean CCI:   {cci_df['cci_score'].mean():.2f}")

# ── MEDICATION COUNT PER PATIENT ───────────────────────────────
print("\nComputing medication counts...")
cohort_meds = all_medications[
    all_medications['PATIENT'].isin(cohort['PATIENT'])
]
med_counts = cohort_meds.groupby('PATIENT').agg(
    n_unique_meds  = ('DESCRIPTION', 'nunique'),
    n_med_records  = ('DESCRIPTION', 'count')
).reset_index()

# Top medications
top_meds = cohort_meds['DESCRIPTION'].value_counts().head(20).reset_index()
top_meds.columns = ['medication', 'frequency']
top_meds.to_csv(r"D:\projects\healthcare\rwe\data\top_medications.csv", index=False)
print(f"✅ Medication data computed")

# ── HEALTHCARE UTILISATION ─────────────────────────────────────
print("Computing healthcare utilisation...")
cohort_enc = all_encounters[
    all_encounters['PATIENT'].isin(cohort['PATIENT'])
]

enc_util = cohort_enc.groupby('PATIENT').agg(
    total_encounters = ('ID', 'count')
).reset_index()

hosp = cohort_enc[
    cohort_enc['ENCOUNTERCLASS'].str.lower().isin(['inpatient', 'emergency'])
].groupby('PATIENT').agg(
    n_hospitalisations = ('ID', 'count')
).reset_index()

print(f"✅ Utilisation data computed")

# ── ASSEMBLE GOLD TABLE ────────────────────────────────────────
print("\nAssembling Gold table...")

gold = cohort.copy()
gold = gold.merge(cci_df, on='PATIENT', how='left')
gold = gold.merge(med_counts, on='PATIENT', how='left')
gold = gold.merge(enc_util, on='PATIENT', how='left')
gold = gold.merge(hosp, on='PATIENT', how='left')

# Fill nulls
gold['n_unique_meds']      = gold['n_unique_meds'].fillna(0).astype(int)
gold['n_med_records']      = gold['n_med_records'].fillna(0).astype(int)
gold['total_encounters']   = gold['total_encounters'].fillna(0).astype(int)
gold['n_hospitalisations'] = gold['n_hospitalisations'].fillna(0).astype(int)
gold['cci_score']          = gold['cci_score'].fillna(0).astype(int)

# CCI risk category
gold['cci_risk_category'] = pd.cut(
    gold['cci_score'],
    bins=[-1, 0, 2, 4, 100],
    labels=['Low (0)', 'Mild (1-2)', 'Moderate (3-4)', 'Severe (5+)']
)

# ── Save to PostgreSQL and CSV ─────────────────────────────────
gold.to_sql(f"{DISEASE_SHORT}_characterised", engine, schema="gold",
            if_exists="replace", index=False)

gold.to_csv(r"D:\projects\healthcare\rwe\data\gold_cohort.csv", index=False)

print(f"\n✅ Gold table saved: gold.{DISEASE_SHORT}_characterised")

# ── PRINT FULL SUMMARY ─────────────────────────────────────────
print("\n" + "=" * 60)
print(f"COHORT CHARACTERISATION — {DISEASE_NAME.upper()}")
print("=" * 60)

print(f"\n📊 POPULATION")
print(f"   Total patients:           {len(gold):,}")
print(f"   Deceased:                 {gold['is_deceased'].sum():,} ({gold['is_deceased'].mean()*100:.1f}%)")

print(f"\n👥 DEMOGRAPHICS")
print(f"   Median age at index:      {gold['age_at_index'].median():.1f} years")
print(f"   Mean age at index:        {gold['age_at_index'].mean():.1f} years")
print(f"   Female:                   {(gold['GENDER']=='F').sum():,} ({(gold['GENDER']=='F').mean()*100:.1f}%)")
print(f"   Male:                     {(gold['GENDER']=='M').sum():,} ({(gold['GENDER']=='M').mean()*100:.1f}%)")

print(f"\n   Age groups:")
print(gold['age_group'].value_counts().sort_index().to_string())

print(f"\n   Race:")
print(gold['RACE'].value_counts().to_string())

print(f"\n🏥 COMORBIDITY (CCI)")
print(f"   Median CCI:               {gold['cci_score'].median():.1f}")
print(f"   Mean CCI:                 {gold['cci_score'].mean():.2f}")
print(f"\n   CCI Risk Categories:")
print(gold['cci_risk_category'].value_counts().sort_index().to_string())

print(f"\n💊 MEDICATIONS")
print(f"   Median unique meds:       {gold['n_unique_meds'].median():.0f}")
print(f"   Mean unique meds:         {gold['n_unique_meds'].mean():.1f}")

print(f"\n🏨 HEALTHCARE UTILISATION")
print(f"   Median total encounters:  {gold['total_encounters'].median():.0f}")
print(f"   Median hospitalisations:  {gold['n_hospitalisations'].median():.0f}")

print("\n✅ GOLD LAYER COMPLETE!")
