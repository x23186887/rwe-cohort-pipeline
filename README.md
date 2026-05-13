# RWE Rare Disease Cohort Pipeline

**A pharmacoepidemiology pipeline replicating a Real World Evidence study workflow**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)
![Synthea](https://img.shields.io/badge/Data-Synthea%20Synthetic%20EMR-green)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

---

## Clinical Context

This project replicates the foundational workflow used by pharmacoepidemiologists
to identify rare disease patient cohorts from electronic medical record (EMR) data.

**Target disease:** Myasthenia Gravis (ICD-10: G70.00, G70.01)
- Rare autoimmune neuromuscular disorder (~20 per 100,000 people)
- Treated by AstraZeneca/Alexion with complement inhibitor eculizumab
- Synthea does not model MG (rare disease) — Type 2 Diabetes used as
  proxy to demonstrate the full pipeline with real data volume

---

## Pipeline Architecture

Synthea EMR (5,000 patients)
↓
PostgreSQL — Bronze Layer (raw ingestion, 15 tables)
↓
PostgreSQL — Silver Layer (SNOMED→ICD-10 mapping, phenotyping algorithm)
↓
PostgreSQL — Gold Layer (CCI, demographics, healthcare utilisation)
↓
Plotly Dash Dashboard + ReportLab PDF Report

---

## Key Methods

| Method | Detail |
|--------|--------|
| Phenotyping | ≥2 coded encounters rule (reduces misclassification bias) |
| Code mapping | SNOMED CT → ICD-10-CM via NLM reference files |
| Comorbidity | Charlson Comorbidity Index (17 weighted conditions) |
| Data source | Synthea synthetic EMR — Massachusetts, n=5,000 |
| Database | PostgreSQL with bronze/silver/gold schema architecture |

---

## Cohort Results (Diabetes Proxy)

| Metric | Value |
|--------|-------|
| Total patients | 433 |
| Median age | 46.6 years |
| Female | 46.7% |
| Median CCI | 3.0 |
| Deceased | 37.2% |
| Median encounters | 150 |

---

## Running the Pipeline

### 1. Prerequisites
- Python 3.10+, PostgreSQL, Java 17+ (for Synthea)

### 2. Generate synthetic data
```bash
cd synthea
.\run_synthea.bat -p 5000 Massachusetts --exporter.csv.export=true
```

### 3. Set up config
```python
# config.py
CONNECTION_STRING = "postgresql://postgres:password@localhost:5433/rwe_db"
SYNTHEA_PATH = r"path\to\synthea\output\csv"
```

### 4. Install dependencies
```bash
pip install pandas sqlalchemy psycopg2-binary plotly dash reportlab scipy numpy
```

### 5. Run pipeline in order
```bash
python 01_load_bronze.py       # Ingest Synthea CSVs → PostgreSQL bronze
python 02_create_silver.py     # SNOMED mapping + cohort definition
python 03_create_gold.py       # CCI + characterisation
python 04_dashboard.py         # Launch dashboard → http://localhost:8050
python 05_generate_report.py   # Generate PDF study report
```

---

## Project Structure
rwe/
├── 01_load_bronze.py         # Bronze layer ingestion
├── 02_create_silver.py       # Silver layer — code mapping & cohort
├── 03_create_gold.py         # Gold layer — characterisation & CCI
├── 04_dashboard.py           # Plotly Dash interactive dashboard
├── 05_generate_report.py     # ReportLab PDF study report
├── config.py                 # DB connection (excluded from Git)
├── data/
│   ├── disease_config.txt
│   └── existing_condition_codes.csv
├── reports/
│   └── rwe_study_report.pdf
└── synthea/                  # Synthea repo (submodule)

---
**Synthetic data only — not for clinical use**