# 05_generate_report.py
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import date
import sys

sys.path.insert(0, r"D:\projects\healthcare\rwe")

print("Generating PDF report...")

gold = pd.read_csv(r"D:\projects\healthcare\rwe\data\gold_cohort.csv")
config = {}
with open(r"D:\projects\healthcare\rwe\data\disease_config.txt") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        config[k] = v
DISEASE_NAME = config["DISEASE_NAME"]

OUTPUT = r"D:\projects\healthcare\rwe\reports\rwe_study_report.pdf"

# ── Colours ────────────────────────────────────────────────────
DARK  = colors.HexColor("#003865")
MED   = colors.HexColor("#0077C8")
LBLUE = colors.HexColor("#E8F4FD")
ORG   = colors.HexColor("#E87722")
GREY  = colors.HexColor("#F7F9FC")
WHITE = colors.white

# ── Styles ─────────────────────────────────────────────────────
S = getSampleStyleSheet()

def style(name, **kw):
    return ParagraphStyle(name, parent=S["Normal"], **kw)

T  = style("T",  fontSize=20, fontName="Helvetica-Bold",
           textColor=WHITE, alignment=TA_CENTER)
SU = style("SU", fontSize=11, fontName="Helvetica",
           textColor=colors.HexColor("#B0C4DE"), alignment=TA_CENTER)
H  = style("H",  fontSize=13, fontName="Helvetica-Bold",
           textColor=DARK, spaceBefore=14, spaceAfter=6)
B  = style("B",  fontSize=9,  fontName="Helvetica",
           textColor=colors.HexColor("#333"), spaceAfter=5,
           leading=15, alignment=TA_JUSTIFY)
BB = style("BB", fontSize=9,  fontName="Helvetica-Bold",
           textColor=colors.HexColor("#333"), spaceAfter=4)
SM = style("SM", fontSize=7,  fontName="Helvetica",
           textColor=colors.grey, alignment=TA_CENTER)

doc   = SimpleDocTemplate(OUTPUT, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm,   bottomMargin=2*cm)
story = []

# ── Title block ────────────────────────────────────────────────
def tbl(data, widths, style_cmds):
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle(style_cmds))
    return t

story.append(tbl(
    [[Paragraph("REAL WORLD EVIDENCE STUDY REPORT", T)]],
    [17*cm],
    [("BACKGROUND",(0,0),(-1,-1),DARK),
     ("TOPPADDING",(0,0),(-1,-1),16),
     ("BOTTOMPADDING",(0,0),(-1,-1),16)]
))
story.append(Spacer(1, 0.25*cm))
story.append(tbl(
    [[Paragraph(f"Disease: {DISEASE_NAME}", SU)]],
    [17*cm],
    [("BACKGROUND",(0,0),(-1,-1),MED),
     ("TOPPADDING",(0,0),(-1,-1),7),
     ("BOTTOMPADDING",(0,0),(-1,-1),7)]
))
story.append(Spacer(1, 0.35*cm))

# Meta table
meta = [
    ["Study Type:",    "Retrospective Cohort Study — Descriptive"],
    ["Data Source:",   "Synthea Synthetic EMR v3.x · Massachusetts · n = 5,000"],
    ["Analysis Date:", str(date.today())],
    ["Pipeline:",      "Bronze → Silver → Gold (PostgreSQL + Python)"],
    ["Status:",        "⚠️  Synthetic Data Only — Not for Clinical Use"],
]
mt = Table(meta, colWidths=[4*cm, 13*cm])
mt.setStyle(TableStyle([
    ("FONTNAME",  (0,0),(0,-1),"Helvetica-Bold"),
    ("FONTSIZE",  (0,0),(-1,-1),8.5),
    ("TEXTCOLOR", (0,0),(0,-1),DARK),
    ("TEXTCOLOR", (1,4),(1,4), ORG),
    ("ROWBACKGROUNDS",(0,0),(-1,-1),[GREY, WHITE]),
    ("TOPPADDING",(0,0),(-1,-1),4),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING",(0,0),(-1,-1),7),
]))
story.append(mt)
story.append(Spacer(1,0.4*cm))
story.append(HRFlowable(width="100%", thickness=2, color=MED))

# ── 1. Objectives ──────────────────────────────────────────────
story.append(Paragraph("1. Study Objectives", H))
story.append(Paragraph(
    f"This study aimed to identify and characterise a patient cohort from synthetic EMR data "
    f"using a standard pharmacoepidemiology pipeline. Target disease: {DISEASE_NAME}. "
    "Objectives: (i) apply SNOMED CT → ICD-10-CM clinical code mappings to identify eligible "
    "patients; (ii) compute baseline demographics and comorbidity burden via the Charlson "
    "Comorbidity Index (CCI); (iii) characterise healthcare utilisation patterns.", B))

# ── 2. Methods ─────────────────────────────────────────────────
story.append(Paragraph("2. Methods", H))
story.append(Paragraph("2.1  Data Source", BB))
story.append(Paragraph(
    "Synthea™ (MITRE Corporation) open-source synthetic patient simulator. Population of 5,000 "
    "patients representing Massachusetts, USA. Data domains: diagnoses, medications, procedures, "
    "observations, encounters. Data is clinically realistic but entirely de-identified and synthetic.", B))

story.append(Paragraph("2.2  Phenotyping Algorithm", BB))
story.append(Paragraph(
    "Patients were identified using SNOMED CT codes mapped to ICD-10-CM equivalents via the NLM "
    "reference mapping. A minimum of two coded encounters bearing the index disease code was "
    "required for inclusion — this two-encounter rule reduces misclassification bias from "
    "incidental or rule-out coding, consistent with published pharmacoepidemiology guidelines.", B))

story.append(Paragraph("2.3  Comorbidity Assessment — Charlson Comorbidity Index", BB))
story.append(Paragraph(
    "The CCI was calculated per patient from conditions recorded in the EMR. Seventeen comorbid "
    "conditions are assigned weights of 1, 2, 3, or 6 and summed. Higher CCI indicates greater "
    "comorbidity burden and predicts 10-year mortality risk. Widely used as a covariate in "
    "pharmacoepidemiology regression models.", B))

story.append(Paragraph("2.4  Statistical Analysis", BB))
story.append(Paragraph(
    "Descriptive statistics only. Continuous variables: median and mean. "
    "Categorical variables: count and percentage. No inferential testing performed.", B))

# ── 3. Results ─────────────────────────────────────────────────
story.append(Paragraph("3. Results", H))

n        = len(gold)
med_age  = gold['age_at_index'].median()
mean_age = gold['age_at_index'].mean()
pct_f    = (gold['GENDER']=='F').mean()*100
med_cci  = gold['cci_score'].median()
mean_cci = gold['cci_score'].mean()
pct_dec  = gold['is_deceased'].mean()*100
med_enc  = gold['total_encounters'].median()
med_hosp = gold['n_hospitalisations'].median()
med_meds = gold['n_unique_meds'].median()

rows = [
    ["Characteristic",                      "Value"],
    ["POPULATION",                           ""],
    ["Total patients in cohort",             f"{n:,}"],
    ["Deceased at analysis date",            f"{gold['is_deceased'].sum():,}  ({pct_dec:.1f}%)"],
    ["",                                     ""],
    ["DEMOGRAPHICS",                         ""],
    ["Median age at index (years)",          f"{med_age:.1f}"],
    ["Mean age at index (years)",            f"{mean_age:.1f}"],
    ["Female",                               f"{(gold['GENDER']=='F').sum():,}  ({pct_f:.1f}%)"],
    ["Male",                                 f"{(gold['GENDER']=='M').sum():,}  ({100-pct_f:.1f}%)"],
    ["",                                     ""],
    ["COMORBIDITY BURDEN (CCI)",             ""],
    ["Median Charlson Comorbidity Index",    f"{med_cci:.1f}"],
    ["Mean Charlson Comorbidity Index",      f"{mean_cci:.2f}"],
    ["CCI = 0  (Low risk)",                  f"{(gold['cci_score']==0).sum():,}  ({(gold['cci_score']==0).mean()*100:.1f}%)"],
    ["CCI 1–2  (Mild)",                      f"{gold['cci_score'].between(1,2).sum():,}  ({gold['cci_score'].between(1,2).mean()*100:.1f}%)"],
    ["CCI 3–4  (Moderate)",                  f"{gold['cci_score'].between(3,4).sum():,}  ({gold['cci_score'].between(3,4).mean()*100:.1f}%)"],
    ["CCI ≥ 5  (Severe)",                    f"{(gold['cci_score']>=5).sum():,}  ({(gold['cci_score']>=5).mean()*100:.1f}%)"],
    ["",                                     ""],
    ["HEALTHCARE UTILISATION",               ""],
    ["Median total encounters",              f"{med_enc:.0f}"],
    ["Median hospitalisations",              f"{med_hosp:.0f}"],
    ["Median unique medications",            f"{med_meds:.0f}"],
]

section_rows = {1, 5, 11, 19}
rt = Table(rows, colWidths=[11*cm, 6*cm])
style_cmds = [
    ("BACKGROUND",  (0,0),(-1,0),  DARK),
    ("TEXTCOLOR",   (0,0),(-1,0),  WHITE),
    ("FONTNAME",    (0,0),(-1,0),  "Helvetica-Bold"),
    ("ALIGN",       (0,0),(-1,0),  "CENTER"),
    ("FONTSIZE",    (0,0),(-1,-1), 8.5),
    ("TOPPADDING",  (0,0),(-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ("LEFTPADDING", (0,0),(-1,-1), 7),
    ("GRID",        (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
    ("LINEBELOW",   (0,0),(-1,0),  1.5, DARK),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, GREY]),
]
for r in section_rows:
    style_cmds += [
        ("BACKGROUND", (0,r),(-1,r), LBLUE),
        ("TEXTCOLOR",  (0,r),(-1,r), DARK),
        ("FONTNAME",   (0,r),(-1,r), "Helvetica-Bold"),
    ]
rt.setStyle(TableStyle(style_cmds))
story.append(rt)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("Table 1. Baseline characteristics of the study cohort.", SM))

# ── 4. Limitations ─────────────────────────────────────────────
story.append(Paragraph("4. Limitations", H))
story.append(Paragraph(
    "Analysis based entirely on Synthea synthetic data — does not reflect real patient populations. "
    "Synthea is calibrated for common diseases; rare diseases (e.g. Myasthenia Gravis) are "
    "under-represented, necessitating use of a proxy condition for pipeline demonstration. "
    "In a production study, methods would be applied to validated real-world sources such as "
    "CPRD, Optum Clinformatics, IBM MarketScan, or MIMIC-IV.", B))

# ── 5. Conclusions ─────────────────────────────────────────────
story.append(Paragraph("5. Conclusions", H))
story.append(Paragraph(
    f"A complete end-to-end RWE cohort pipeline was successfully implemented, identifying "
    f"{n:,} patients meeting the {DISEASE_NAME} phenotyping criteria (median age {med_age:.0f} yrs, "
    f"median CCI {med_cci:.0f}, median {med_enc:.0f} total encounters). The pipeline demonstrated "
    "full data flow from raw EMR ingestion through bronze/silver/gold layers, applying SNOMED CT → "
    "ICD-10-CM mappings, computing the Charlson Comorbidity Index, and producing an interactive "
    "Plotly Dash dashboard and this structured study report — replicating the foundational "
    "methodology of published pharmacoepidemiology studies.", B))

story.append(Spacer(1, 0.5*cm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    "⚠️ DISCLAIMER: Generated from entirely synthetic data (Synthea) for portfolio demonstration "
    "only. Does not contain or represent real patient information. Not for clinical, regulatory, "
    "or commercial use.", SM))

doc.build(story)
print(f"\n✅ PDF saved to: {OUTPUT}")
print("Open File Explorer → D:\\projects\\healthcare\\rwe\\reports\\")
print("\n✅ REPORT COMPLETE!")