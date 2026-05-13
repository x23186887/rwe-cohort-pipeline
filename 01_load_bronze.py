# 01_load_bronze.py
import pandas as pd
from sqlalchemy import create_engine, text
import os, sys

sys.path.insert(0, r"D:\projects\healthcare\rwe")
from config import CONNECTION_STRING, SYNTHEA_PATH

print("=" * 60)
print("BRONZE LAYER INGESTION")
print("=" * 60)

engine = create_engine(CONNECTION_STRING)

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("Connected to rwe_db!")

# Skip very large files that would take too long
SKIP_TABLES = ["claims_transactions", "claims", "observations"]

tables = [
    "patients", "conditions", "medications", "encounters",
    "procedures", "careplans", "imaging_studies", "immunizations",
    "allergies", "organizations", "payers", "providers",
    "payer_transitions", "devices", "supplies"
]

quality_report = []

for table_name in tables:
    filepath = os.path.join(SYNTHEA_PATH, f"{table_name}.csv")

    if not os.path.exists(filepath):
        print(f"Skipping {table_name} — file not found")
        continue

    print(f"\nLoading {table_name}...")

    try:
        df = pd.read_csv(filepath, low_memory=False)
        null_pct = round(
            df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2
        )

        df.to_sql(
            f"raw_{table_name}", engine,
            schema="bronze", if_exists="replace", index=False,
            chunksize=10000
        )

        quality_report.append({
            "table": table_name,
            "rows": len(df),
            "columns": len(df.columns),
            "null_pct": null_pct
        })
        print(f"   {len(df):,} rows | {len(df.columns)} cols | {null_pct}% nulls")

    except Exception as e:
        print(f"   ❌ Error loading {table_name}: {e}")

print("\n" + "=" * 60)
print("DATA QUALITY BASELINE REPORT")
print("=" * 60)
qdf = pd.DataFrame(quality_report)
print(qdf.to_string(index=False))
qdf.to_csv(r"D:\projects\healthcare\rwe\data\bronze_quality_report.csv", index=False)
print("\n BRONZE LAYER COMPLETE!")