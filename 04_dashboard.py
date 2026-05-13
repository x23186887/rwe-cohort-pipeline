# 04_dashboard.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output

print("Loading data...")
gold = pd.read_csv(r"D:\projects\healthcare\rwe\data\gold_cohort.csv")

config = {}
with open(r"D:\projects\healthcare\rwe\data\disease_config.txt") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        config[k] = v
DISEASE_NAME = config["DISEASE_NAME"]

# ── Colours ────────────────────────────────────────────────────
C = {
    "dark":    "#003865",
    "mid":     "#0077C8",
    "light":   "#00A3E0",
    "orange":  "#E87722",
    "bg":      "#F7F9FC",
    "white":   "#FFFFFF",
    "lblue":   "#E8F4FD",
}

# ── KPIs ───────────────────────────────────────────────────────
N          = len(gold)
MED_AGE    = gold['age_at_index'].median()
PCT_F      = (gold['GENDER'] == 'F').mean() * 100
MED_CCI    = gold['cci_score'].median()
PCT_DEC    = gold['is_deceased'].mean() * 100
MED_ENC    = gold['total_encounters'].median()

# ── Helpers ────────────────────────────────────────────────────
CARD = lambda label, val: html.Div(style={
    "background": C["white"], "borderRadius": "10px",
    "padding": "18px 22px", "flex": "1", "minWidth": "130px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
    "borderTop": f"4px solid {C['mid']}"
}, children=[
    html.P(label, style={"color": "#777", "margin": "0 0 4px",
                         "fontSize": "11px", "fontWeight": "700",
                         "textTransform": "uppercase", "letterSpacing": "0.6px"}),
    html.H2(val,  style={"color": C["dark"], "margin": 0, "fontSize": "26px"})
])

CHART_BOX = lambda title, graph_id, flex="1", minw="280px": html.Div(
    style={"flex": flex, "minWidth": minw, "background": C["white"],
           "borderRadius": "10px", "padding": "16px",
           "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"},
    children=[
        html.H3(title, style={"color": C["dark"], "margin": "0 0 10px",
                              "fontSize": "14px", "fontWeight": "700"}),
        dcc.Graph(id=graph_id, config={"displayModeBar": False})
    ]
)

LAYOUT = {"margin": {"t": 10, "b": 35, "l": 40, "r": 10},
           "plot_bgcolor": C["bg"], "paper_bgcolor": C["white"],
           "showlegend": False, "height": 250,
           "font": {"family": "Segoe UI, Arial", "size": 11}}

# ── App ────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "RWE Cohort Dashboard"

app.layout = html.Div(
    style={"background": C["bg"], "fontFamily": "Segoe UI, Arial, sans-serif",
           "minHeight": "100vh"},
    children=[

        # ── Header ──────────────────────────────────────────────
        html.Div(style={"background": C["dark"], "padding": "18px 36px"}, children=[
            html.H1("Real World Evidence — Cohort Dashboard",
                    style={"color": C["white"], "margin": 0, "fontSize": "22px"}),
            html.P(f"Disease: {DISEASE_NAME}  |  n = {N:,} patients",
                   style={"color": "#88AACC", "margin": "4px 0 0", "fontSize": "13px"})
        ]),

        # ── KPI Row ──────────────────────────────────────────────
        html.Div(style={"display": "flex", "gap": "14px",
                        "padding": "20px 36px", "flexWrap": "wrap"}, children=[
            CARD("Total Patients",     f"{N:,}"),
            CARD("Median Age",         f"{MED_AGE:.0f} yrs"),
            CARD("Female",             f"{PCT_F:.0f}%"),
            CARD("Median CCI",         f"{MED_CCI:.0f}"),
            CARD("Deceased",           f"{PCT_DEC:.0f}%"),
            CARD("Median Encounters",  f"{MED_ENC:.0f}"),
        ]),

        # ── Filters ──────────────────────────────────────────────
        html.Div(style={"padding": "0 36px 14px", "display": "flex",
                        "gap": "24px", "alignItems": "center"}, children=[
            html.B("Filters:", style={"color": C["dark"]}),
            html.Div([
                html.Label("Gender", style={"marginRight": "6px", "fontSize": "13px"}),
                dcc.Dropdown(
                    id="dd-gender",
                    options=[{"label": "All",    "value": "ALL"},
                             {"label": "Female", "value": "F"},
                             {"label": "Male",   "value": "M"}],
                    value="ALL", clearable=False,
                    style={"width": "130px", "fontSize": "13px"}
                )
            ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
            html.Div([
                html.Label("Race", style={"marginRight": "6px", "fontSize": "13px"}),
                dcc.Dropdown(
                    id="dd-race",
                    options=[{"label": "All", "value": "ALL"}] + [
                        {"label": r.title(), "value": r}
                        for r in sorted(gold['RACE'].dropna().unique())
                    ],
                    value="ALL", clearable=False,
                    style={"width": "160px", "fontSize": "13px"}
                )
            ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
            html.Div([
                html.Label("CCI Risk", style={"marginRight": "6px", "fontSize": "13px"}),
                dcc.Dropdown(
                    id="dd-cci",
                    options=[{"label": "All",          "value": "ALL"},
                             {"label": "Low (0)",       "value": "Low (0)"},
                             {"label": "Mild (1-2)",    "value": "Mild (1-2)"},
                             {"label": "Moderate (3-4)","value": "Moderate (3-4)"},
                             {"label": "Severe (5+)",   "value": "Severe (5+)"}],
                    value="ALL", clearable=False,
                    style={"width": "160px", "fontSize": "13px"}
                )
            ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
        ]),

        # ── Row 1: Age hist | Gender pie | Race bar ──────────────
        html.Div(style={"padding": "0 36px", "display": "flex",
                        "gap": "14px", "flexWrap": "wrap"}, children=[
            CHART_BOX("Age Distribution at Index Date", "fig-age",    flex="1.4"),
            CHART_BOX("Sex Distribution",               "fig-gender", flex="0.7"),
            CHART_BOX("Race / Ethnicity",               "fig-race",   flex="1"),
        ]),

        # ── Row 2: CCI bar | Scatter | Top meds ─────────────────
        html.Div(style={"padding": "14px 36px 20px", "display": "flex",
                        "gap": "14px", "flexWrap": "wrap"}, children=[
            CHART_BOX("Charlson Comorbidity Index",        "fig-cci",     flex="1"),
            CHART_BOX("Encounters vs Age (sized by CCI)",  "fig-scatter", flex="1.4"),
            CHART_BOX("CCI Components — % of Cohort",      "fig-comorbid",flex="1"),
        ]),

        # ── Footer ───────────────────────────────────────────────
        html.Div(style={"padding": "10px 36px 20px",
                        "color": "#aaa", "fontSize": "11px", "textAlign": "center"},
                 children=[html.P(
                     "⚠️ SYNTHETIC DATA ONLY — Synthea EMR | Not for clinical use"
                 )])
    ]
)

# ── Callback ───────────────────────────────────────────────────
@app.callback(
    [Output("fig-age",      "figure"),
     Output("fig-gender",   "figure"),
     Output("fig-race",     "figure"),
     Output("fig-cci",      "figure"),
     Output("fig-scatter",  "figure"),
     Output("fig-comorbid", "figure")],
    [Input("dd-gender", "value"),
     Input("dd-race",   "value"),
     Input("dd-cci",    "value")]
)
def update(gender, race, cci_cat):
    df = gold.copy()
    if gender != "ALL":
        df = df[df['GENDER'] == gender]
    if race != "ALL":
        df = df[df['RACE'] == race]
    if cci_cat != "ALL":
        df = df[df['cci_risk_category'] == cci_cat]

    empty = go.Figure().update_layout(**LAYOUT)
    if len(df) == 0:
        return [empty] * 6

    # 1. Age histogram
    fig_age = px.histogram(df, x="age_at_index", nbins=20,
                           color_discrete_sequence=[C["mid"]],
                           labels={"age_at_index": "Age (years)", "count": "Patients"})
    fig_age.add_vline(x=df['age_at_index'].median(), line_dash="dash",
                      line_color=C["orange"],
                      annotation_text=f"Median {df['age_at_index'].median():.0f}y",
                      annotation_position="top right")
    fig_age.update_layout(**LAYOUT)

    # 2. Gender pie
    gc = df['GENDER'].map({'F': 'Female', 'M': 'Male'}).value_counts().reset_index()
    gc.columns = ['sex', 'n']
    fig_gender = px.pie(gc, names='sex', values='n',
                        color_discrete_sequence=[C["light"], C["orange"]],
                        hole=0.45)
    fig_gender.update_layout(**{**LAYOUT, "showlegend": True,
                                "legend": {"orientation": "h", "y": -0.15}})

    # 3. Race bar
    rc = df['RACE'].value_counts().reset_index()
    rc.columns = ['race', 'n']
    rc['race'] = rc['race'].str.title()
    fig_race = px.bar(rc.head(7), x='n', y='race', orientation='h',
                      color_discrete_sequence=[C["dark"]],
                      labels={"n": "Patients", "race": ""})
    fig_race.update_layout(**{**LAYOUT, "yaxis": {"autorange": "reversed"}})

    # 4. CCI risk bar
    cci_order = ['Low (0)', 'Mild (1-2)', 'Moderate (3-4)', 'Severe (5+)']
    cci_colors = {"Low (0)": "#4CAF50", "Mild (1-2)": C["light"],
                  "Moderate (3-4)": C["orange"], "Severe (5+)": "#D32F2F"}
    cci_counts = df['cci_risk_category'].value_counts().reindex(cci_order, fill_value=0).reset_index()
    cci_counts.columns = ['cat', 'n']
    fig_cci = go.Figure(go.Bar(
        x=cci_counts['cat'], y=cci_counts['n'],
        marker_color=[cci_colors[c] for c in cci_counts['cat']],
        text=cci_counts['n'], textposition='outside'
    ))
    fig_cci.update_layout(**{**LAYOUT,
                             "xaxis_title": "CCI Risk Category",
                             "yaxis_title": "Patients"})

    # 5. Scatter age vs encounters
    sample = df.sample(min(len(df), 400), random_state=42)
    fig_scatter = px.scatter(
        sample, x="age_at_index", y="total_encounters",
        color="GENDER", size="cci_score",
        color_discrete_map={"F": C["light"], "M": C["orange"]},
        size_max=18, opacity=0.65,
        labels={"age_at_index": "Age at Index",
                "total_encounters": "Total Encounters",
                "GENDER": "Sex", "cci_score": "CCI"}
    )
    fig_scatter.update_layout(**{**LAYOUT, "showlegend": True,
                                 "plot_bgcolor": "#F0F4F8"})

    # 6. CCI components heatmap-style bar
    cci_component_cols = [c for c in df.columns if c in [
        'myocardial_infarction','congestive_heart_failure','peripheral_vascular',
        'cerebrovascular','dementia','copd','rheumatologic','peptic_ulcer',
        'mild_liver','diabetes_uncomplicated','diabetes_complicated',
        'hemiplegia','renal_disease','malignancy','severe_liver',
        'metastatic_tumor','aids'
    ]]
    if cci_component_cols:
        comp_pct = (df[cci_component_cols].mean() * 100).sort_values(ascending=True)
        comp_pct.index = [i.replace('_', ' ').title() for i in comp_pct.index]
        fig_comorbid = go.Figure(go.Bar(
            x=comp_pct.values,
            y=comp_pct.index,
            orientation='h',
            marker_color=C["mid"],
            text=[f"{v:.0f}%" for v in comp_pct.values],
            textposition='outside'
        ))
        fig_comorbid.update_layout(**{**LAYOUT,
                                      "xaxis_title": "% of Cohort",
                                      "height": 260,
                                      "yaxis": {"autorange": "reversed"}})
    else:
        fig_comorbid = empty

    return fig_age, fig_gender, fig_race, fig_cci, fig_scatter, fig_comorbid


if __name__ == "__main__":
    print("\n" + "="*55)
    print("DASHBOARD READY!")
    print("Open browser → http://127.0.0.1:8050")
    print("Press Ctrl+C to stop")
    print("="*55 + "\n")
    app.run(debug=False, port=8050)
    