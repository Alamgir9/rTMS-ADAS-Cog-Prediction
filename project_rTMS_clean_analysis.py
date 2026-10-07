# -*- coding: utf-8 -*-

"""
Clean rTMS ADAS-Cog prediction analysis.

Generated from project_rTMS_Mac_fixed-8.html with duplicate/obsolete plotting
cells removed. The analysis uses ADAS-Cog-Recog Total Score as the corrected
11-component ADAS-Cog total. Main manuscript figures 1-8 and supplementary
Figure S1 are saved as both 300-dpi PNG and vector PDF files.

Run:
    python project_rTMS_clean_analysis.py

Optional:
    Set environment variable RTMS_DATA_FILE to the Excel data file path.
"""

import os
import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from IPython.display import display

pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 100)

sns.set_theme(style="whitegrid", context="notebook")

RANDOM_STATE = 20260822

print("Packages imported successfully.")


# ============================================================
# DATA FILE AND OUTPUT LOCATIONS
# ============================================================

# Use RTMS_DATA_FILE when supplied; otherwise check repository data/
# and common local filenames beside this script.
script_dir = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

_data_candidates = []
if os.environ.get("RTMS_DATA_FILE"):
    _data_candidates.append(Path(os.environ["RTMS_DATA_FILE"]).expanduser())

_data_candidates.extend([
    script_dir / "data" / "rTMS participants pre-post info.xlsx",
    script_dir / "data" / "rTMS participants pre-post info(9).xlsx",
    script_dir / "rTMS participants pre-post info.xlsx",
    script_dir / "rTMS participants pre-post info(9).xlsx",
])

FILE_PATH = next((p for p in _data_candidates if p.is_file()), None)
if FILE_PATH is None:
    raise FileNotFoundError(
        "Could not find the rTMS Excel file. Set RTMS_DATA_FILE to its full path."
    )

DATA_DIR = Path(os.environ.get("RTMS_OUTPUT_DIR", str(script_dir / "outputs"))).expanduser()
DATA_DIR.mkdir(parents=True, exist_ok=True)
TOTAL_COLUMN = "ADAS-Cog-Recog Total Score"

MANUSCRIPT_FIGURE_DIR = DATA_DIR / "manuscript_figures"
MANUSCRIPT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

from matplotlib.lines import Line2D
import statsmodels.api as sm

sns.set_theme(context="paper", style="whitegrid", font_scale=1.15)
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "legend.title_fontsize": 9,
})

def save_manuscript_figure(fig, file_stem):
    png_path = MANUSCRIPT_FIGURE_DIR / f"{file_stem}.png"
    pdf_path = MANUSCRIPT_FIGURE_DIR / f"{file_stem}.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    print("Saved PNG:", png_path)
    print("Saved PDF:", pdf_path)

HORIZON_LABELS = {
    "y_8": "8 weeks",
    "y_16": "16 weeks",
    "y_24": "24 weeks",
    "Overall": "Overall",
}
HORIZON_ORDER = ["8 weeks", "16 weeks", "24 weeks", "Overall"]

print("Data file:", FILE_PATH)
N_JOBS = int(os.environ.get("RTMS_N_JOBS", "-1"))
print("Figure folder:", MANUSCRIPT_FIGURE_DIR)
print("Parallel jobs:", N_JOBS)



# ============================================================
# SOURCE CELL In [4]:
# ============================================================
excel_file = pd.ExcelFile(FILE_PATH)

print("Available sheets:")
for sheet in excel_file.sheet_names:
    print("-", sheet)



# ============================================================
# SOURCE CELL In [5]:
# ============================================================
SHEET_NAME = "weston_export-2"

df_raw = pd.read_excel(
    FILE_PATH,
    sheet_name=SHEET_NAME
)

print("Raw dataset dimensions:", df_raw.shape)
print("Number of columns:", df_raw.shape[1])

display(df_raw.head())



# ============================================================
# SOURCE CELL In [6]:
# ============================================================
print("Column names:\n")

for number, column in enumerate(df_raw.columns, start=1):
    print(f"{number:02d}. {column}")

print("\nData types:")
display(df_raw.dtypes.to_frame("Data type"))



# ============================================================
# SOURCE CELL In [7]:
# ============================================================
df = df_raw.copy()

# Remove accidental spaces from column names
df.columns = df.columns.str.strip()

# Identify text-like columns
text_columns = [
    "Participant",
    "Participant Treatment Group",
    "Participant Gender",
    "Sequence"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
        .replace({
            "": pd.NA,
            " ": pd.NA,
            "NA": pd.NA,
            "N/A": pd.NA
        })
    )

# Replace empty or whitespace-only cells throughout the dataset
df = df.replace(r"^\s*$", np.nan, regex=True)

print("Text formatting standardized.")



# ============================================================
# SOURCE CELL In [8]:
# ============================================================
adas_columns = [
    column for column in df.columns
    if column.startswith("ADAS-Cog")
]

numeric_columns = ["Participant Age"] + adas_columns

conversion_report = []

for column in numeric_columns:
    nonmissing_before = df[column].notna().sum()

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    nonmissing_after = df[column].notna().sum()

    conversion_report.append({
        "Variable": column,
        "Nonmissing before": nonmissing_before,
        "Numeric after": nonmissing_after,
        "Values converted to missing":
            nonmissing_before - nonmissing_after
    })

conversion_report = pd.DataFrame(conversion_report)

display(conversion_report)

print("Number of ADAS-Cog variables:", len(adas_columns))



# ============================================================
# SOURCE CELL In [10]:
# ============================================================
df["Site"] = (
    df["Participant"]
    .str.split("-")
    .str[0]
)

print("Participants by site and treatment group:")

participant_information = (
    df[
        [
            "Participant",
            "Site",
            "Participant Treatment Group"
        ]
    ]
    .drop_duplicates("Participant")
)

display(
    pd.crosstab(
        participant_information["Site"],
        participant_information["Participant Treatment Group"],
        margins=True
    )
)



# ============================================================
# SOURCE CELL In [12]:
# ============================================================
visit_summary = (
    df.groupby("Sequence", dropna=False)
    .agg(
        Rows=("Participant", "size"),
        Participants=("Participant", "nunique"),
        ADAS_total_available=(
            TOTAL_COLUMN,
            lambda x: x.notna().sum()
        )
    )
    .sort_values("Rows", ascending=False)
)

display(visit_summary)



# ============================================================
# SOURCE CELL In [13]:
# ============================================================
unblinded_mask = (
    df["Sequence"]
    .str.startswith("Unblinded", na=False)
)

print("Unblinded rows excluded:", unblinded_mask.sum())

df_blinded = df.loc[~unblinded_mask].copy()

print("Rows retained:", len(df_blinded))
print(
    "Participants retained:",
    df_blinded["Participant"].nunique()
)



# ============================================================
# SOURCE CELL In [14]:
# ============================================================
duplicate_mask = df_blinded.duplicated(
    subset=["Participant", "Sequence"],
    keep=False
)

duplicate_visits = (
    df_blinded.loc[
        duplicate_mask,
        [
            "Participant",
            "Sequence",
            "Participant Treatment Group",
            TOTAL_COLUMN
        ] + [
            column for column in adas_columns
            if column != TOTAL_COLUMN
        ]
    ]
    .sort_values(["Participant", "Sequence"])
)

print(
    "Number of rows belonging to duplicate participant-visits:",
    duplicate_mask.sum()
)

display(duplicate_visits)



# ============================================================
# SOURCE CELL In [15]:
# ============================================================
consistency_variables = [
    "Participant Treatment Group",
    "Participant Gender",
    "Participant Age",
    "Site"
]

consistency_results = []

for variable in consistency_variables:
    maximum_unique = (
        df_blinded.groupby("Participant")[variable]
        .nunique(dropna=True)
        .max()
    )

    inconsistent_participants = (
        df_blinded.groupby("Participant")[variable]
        .nunique(dropna=True)
        .loc[lambda x: x > 1]
        .index
        .tolist()
    )

    consistency_results.append({
        "Variable": variable,
        "Maximum values within a participant": maximum_unique,
        "Number inconsistent": len(inconsistent_participants),
        "Inconsistent participants": inconsistent_participants
    })

display(pd.DataFrame(consistency_results))



# ============================================================
# SOURCE CELL In [16]:
# ============================================================
metadata_columns = [
    "Participant Treatment Group",
    "Participant Age",
    "Participant Gender",
    "Site"
]

aggregation_rules = {
    column: "mean"
    for column in adas_columns
}

aggregation_rules.update({
    column: "first"
    for column in metadata_columns
})

df_clean = (
    df_blinded
    .groupby(
        ["Participant", "Sequence"],
        as_index=False,
        dropna=False
    )
    .agg(aggregation_rules)
)

print("Rows before duplicate resolution:", len(df_blinded))
print("Rows after duplicate resolution:", len(df_clean))
print("Participants:", df_clean["Participant"].nunique())



# ============================================================
# SOURCE CELL In [17]:
# ============================================================
missingness = (
    df_clean.isna()
    .mean()
    .mul(100)
    .sort_values(ascending=False)
    .rename("Missing percentage")
    .to_frame()
)

display(missingness.round(2))



# ============================================================
# FIGURE 1
# ============================================================
# ============================================================
# FIGURE 1
# PARTICIPANT AND ADAS-COG DATA AVAILABILITY
# ============================================================

VISIT_ORDER = [
    "Baseline Assessment",
    "3 Week Assessment",
    "5 Week Assessment",
    "8 weeks post treatment",
    "16 weeks post treatment",
    "24 weeks post treatment"
]

VISIT_DISPLAY_LABELS = {
    "Baseline Assessment":
        "Baseline",

    "3 Week Assessment":
        "Week 3",

    "5 Week Assessment":
        "Week 5",

    "8 weeks post treatment":
        "8 weeks post-treatment",

    "16 weeks post treatment":
        "16 weeks post-treatment",

    "24 weeks post treatment":
        "24 weeks post-treatment"
}


visit_availability = (
    df_clean.loc[
        df_clean[
            "Sequence"
        ].isin(
            VISIT_ORDER
        )
    ]
    .groupby(
        "Sequence"
    )
    .agg(
        Participants=(
            "Participant",
            "nunique"
        ),

        ADAS_Cog_available=(
            TOTAL_COLUMN,
            lambda values:
                values.notna().sum()
        )
    )
    .reindex(
        VISIT_ORDER
    )
)


visit_availability.index = [
    VISIT_DISPLAY_LABELS[index]
    for index
    in visit_availability.index
]


fig, ax = plt.subplots(
    figsize=(9, 5.5)
)

y_positions = np.arange(
    len(
        visit_availability
    )
)

bar_height = 0.36


ax.barh(
    y_positions
    -
    bar_height / 2,

    visit_availability[
        "Participants"
    ],

    height=bar_height,

    label=(
        "Assessment record available"
    )
)


ax.barh(
    y_positions
    +
    bar_height / 2,

    visit_availability[
        "ADAS_Cog_available"
    ],

    height=bar_height,

    label=(
        "ADAS-Cog total available"
    )
)


ax.set_yticks(
    y_positions
)

ax.set_yticklabels(
    visit_availability.index
)

ax.set_xlabel(
    "Number of participants"
)

ax.set_ylabel(
    "Assessment"
)

ax.set_title(
    "Participant and ADAS-Cog Data Availability"
)

ax.legend(
    frameon=False
)

ax.grid(
    axis="x",
    alpha=0.25
)

ax.grid(
    axis="y",
    visible=False
)

fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure1_availability"
)


plt.show()



# ============================================================
# SOURCE CELL In [20]:
# ============================================================
qc_summary = pd.Series({
    "Raw rows": len(df_raw),
    "Clean blinded rows": len(df_clean),
    "Participants": df_clean["Participant"].nunique(),
    "Treatment groups":
        df_clean["Participant Treatment Group"].nunique(),
    "Sites": df_clean["Site"].nunique(),
    "ADAS-Cog variables": len(adas_columns),
    "Remaining duplicate participant-visits":
        df_clean.duplicated(
            ["Participant", "Sequence"]
        ).sum()
})

display(qc_summary.to_frame("Value"))



# ============================================================
# SOURCE CELL In [21]:
# ============================================================
VISITS = {
    "baseline": "Baseline Assessment",
    "week3": "3 Week Assessment",
    "week5": "5 Week Assessment",
    "week8": "8 weeks post treatment",
    "week16": "16 weeks post treatment",
    "week24": "24 weeks post treatment"
}

for short_name, full_name in VISITS.items():
    available = (
        df_clean["Sequence"]
        .eq(full_name)
        .sum()
    )

    print(f"{short_name:10s}: {full_name:30s} rows = {available}")



# ============================================================
# SOURCE CELL In [22]:
# ============================================================
DOMAIN_MAP = {
    "ADAS-Cog Recall": "recall",
    "ADAS-Cog Naming": "naming",
    "ADAS-Cog Commands": "commands",
    "ADAS-Cog Const. Praxis": "constructional_praxis",
    "ADAS-Cog Idea. Praxis": "ideational_praxis",
    "ADAS-Cog Orientation": "orientation",
    "ADAS-Cog Word Recognition": "word_recognition",
    "ADAS-Cog Language": "language",
    "ADAS-Cog Comprehension": "comprehension",
    "ADAS-Cog Word Finding": "word_finding",
    "ADAS-Cog RTI": "rti"
}

DOMAIN_COLUMNS = list(DOMAIN_MAP.keys())
TOTAL_COLUMN = "ADAS-Cog-Recog Total Score"
SCORE_COLUMNS = [TOTAL_COLUMN] + DOMAIN_COLUMNS

missing_domain_columns = [
    column for column in SCORE_COLUMNS
    if column not in df_clean.columns
]

if missing_domain_columns:
    raise KeyError(
        "Missing expected score columns: "
        + ", ".join(missing_domain_columns)
    )

print("Number of individual domains:", len(DOMAIN_COLUMNS))
print("Domains used:")

for original, short in DOMAIN_MAP.items():
    print(f"- {short}: {original}")



# ============================================================
# SOURCE CELL In [23]:
# ============================================================
analysis_long = df_clean.loc[
    df_clean["Sequence"].isin(VISITS.values())
].copy()

visit_availability = (
    analysis_long
    .groupby("Sequence")
    .agg(
        Rows=("Participant", "size"),
        Participants=("Participant", "nunique"),
        Total_score_available=(
            TOTAL_COLUMN,
            lambda x: x.notna().sum()
        )
    )
    .reindex(VISITS.values())
)

display(visit_availability)



# ============================================================
# SOURCE CELL In [24]:
# ============================================================
metadata = (
    analysis_long
    .sort_values(["Participant", "Sequence"])
    .groupby("Participant", as_index=True)
    .agg({
        "Participant Treatment Group": "first",
        "Participant Age": "first",
        "Participant Gender": "first",
        "Site": "first"
    })
    .rename(columns={
        "Participant Treatment Group": "treatment",
        "Participant Age": "age",
        "Participant Gender": "sex",
        "Site": "site"
    })
)

print("Metadata dimensions:", metadata.shape)

display(metadata.head())



# ============================================================
# SOURCE CELL In [25]:
# ============================================================
visit_prefixes = {
    VISITS["baseline"]: "b",
    VISITS["week3"]: "w3",
    VISITS["week5"]: "w5",
    VISITS["week8"]: "f8",
    VISITS["week16"]: "f16",
    VISITS["week24"]: "f24"
}

score_short_names = {
    TOTAL_COLUMN: "total",
    **DOMAIN_MAP
}

wide_scores = analysis_long.pivot(
    index="Participant",
    columns="Sequence",
    values=SCORE_COLUMNS
)

new_column_names = []

for score_name, visit_name in wide_scores.columns:
    score_short = score_short_names[score_name]
    visit_short = visit_prefixes[visit_name]

    new_column_names.append(
        f"{visit_short}_{score_short}"
    )

wide_scores.columns = new_column_names

model_data = metadata.join(
    wide_scores,
    how="left"
)

model_data.index.name = "Participant"

print("Participant-level dimensions:", model_data.shape)

display(model_data.head())



# ============================================================
# SOURCE CELL In [26]:
# ============================================================
duplicated_columns = model_data.columns[
    model_data.columns.duplicated()
].tolist()

print("Duplicated columns:", duplicated_columns)

if duplicated_columns:
    raise ValueError(
        "Duplicate columns were created during reshaping."
    )



# ============================================================
# SOURCE CELL In [27]:
# ============================================================
domain_short_names = list(DOMAIN_MAP.values())

for domain in domain_short_names:
    model_data[f"d3_{domain}"] = (
        model_data[f"w3_{domain}"]
        - model_data[f"b_{domain}"]
    )

    model_data[f"d5_{domain}"] = (
        model_data[f"w5_{domain}"]
        - model_data[f"b_{domain}"]
    )

print(
    "Early domain-change variables created:",
    2 * len(domain_short_names)
)
# ============================================================
# ADD TOTAL-SCORE EARLY CHANGE VARIABLES
# ============================================================

model_data["d3_total"] = (
    model_data["w3_total"]
    - model_data["b_total"]
)

model_data["d5_total"] = (
    model_data["w5_total"]
    - model_data["b_total"]
)

print("Early total-score changes created.")

display(
    model_data[
        [
            "b_total",
            "w3_total",
            "w5_total",
            "d3_total",
            "d5_total"
        ]
    ].head()
)



# ============================================================
# SOURCE CELL In [28]:
# ============================================================
model_data["y_8"] = (
    model_data["f8_total"]
    - model_data["b_total"]
)

model_data["y_16"] = (
    model_data["f16_total"]
    - model_data["b_total"]
)

model_data["y_24"] = (
    model_data["f24_total"]
    - model_data["b_total"]
)

OUTCOME_COLUMNS = [
    "y_8",
    "y_16",
    "y_24"
]

print("Outcomes created:", OUTCOME_COLUMNS)



# ============================================================
# SOURCE CELL In [29]:
# ============================================================
BASELINE_DOMAIN_FEATURES = [
    f"b_{domain}"
    for domain in domain_short_names
]

WEEK3_CHANGE_FEATURES = [
    f"d3_{domain}"
    for domain in domain_short_names
]

WEEK5_CHANGE_FEATURES = [
    f"d5_{domain}"
    for domain in domain_short_names
]

NUMERIC_FEATURES = (
    ["age", "b_total"]
    + BASELINE_DOMAIN_FEATURES
    + WEEK3_CHANGE_FEATURES
    + WEEK5_CHANGE_FEATURES
)

CATEGORICAL_FEATURES = [
    "sex",
    "treatment",
    "site"
]

ALL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

print("Numeric predictors:", len(NUMERIC_FEATURES))
print("Categorical predictors:", len(CATEGORICAL_FEATURES))
print("Total pre-encoding predictors:", len(ALL_FEATURES))



# ============================================================
# SOURCE CELL In [30]:
# ============================================================
model_landmark = model_data.dropna(
    subset=ALL_FEATURES
).copy()

print(
    "Participants with complete baseline/week-3/week-5 predictors:",
    len(model_landmark)
)

print("\nBy treatment group:")

display(
    model_landmark["treatment"]
    .value_counts()
    .sort_index()
    .to_frame("Participants")
)



# ============================================================
# SOURCE CELL In [31]:
# ============================================================
outcome_availability = pd.DataFrame({
    "Outcome": OUTCOME_COLUMNS,
    "Available": [
        model_landmark[column].notna().sum()
        for column in OUTCOME_COLUMNS
    ],
    "Missing": [
        model_landmark[column].isna().sum()
        for column in OUTCOME_COLUMNS
    ]
})

outcome_availability["Available percentage"] = (
    100
    * outcome_availability["Available"]
    / len(model_landmark)
)

display(
    outcome_availability.round(1)
)



# ============================================================
# SOURCE CELL In [33]:
# ============================================================
model_complete = model_landmark.dropna(
    subset=OUTCOME_COLUMNS
).copy()

print(
    "Participants with all three future outcomes:",
    len(model_complete)
)

display(
    model_complete["treatment"]
    .value_counts()
    .sort_index()
    .to_frame("Participants")
)



# ============================================================
# SOURCE CELL In [34]:
# ============================================================
# ============================================================
# SUPERVISOR REVISION:
# PARTICIPANT FLOW, MISSINGNESS, AND EXCLUSION AUDIT
# ============================================================

LANDMARK_FEATURES = (
    ["age", "b_total"]
    + BASELINE_DOMAIN_FEATURES
    + WEEK3_CHANGE_FEATURES
    + WEEK5_CHANGE_FEATURES
    + ["sex", "treatment", "site"]
)

# ------------------------------------------------------------
# 1. Overall study flow
# ------------------------------------------------------------

flow_summary = pd.DataFrame({
    "Stage": [
        "Randomized / baseline participants",
        "Complete Week-5 landmark predictors",
        "Complete all three future outcomes"
    ],
    "N": [
        model_data.index.nunique(),
        model_landmark.index.nunique(),
        model_complete.index.nunique()
    ]
})

display(flow_summary)


# ------------------------------------------------------------
# 2. Missingness BEFORE complete-case restriction
# ------------------------------------------------------------

predictor_missingness = (
    model_data[LANDMARK_FEATURES]
    .isna()
    .sum()
    .sort_values(ascending=False)
    .rename("Missing N")
    .to_frame()
)

predictor_missingness["Missing %"] = (
    100
    * predictor_missingness["Missing N"]
    / len(model_data)
)

display(
    predictor_missingness.loc[
        predictor_missingness["Missing N"] > 0
    ].round(1)
)


# ------------------------------------------------------------
# 3. Outcome missingness among the 101 landmark participants
# ------------------------------------------------------------

outcome_missingness = pd.DataFrame({
    "Outcome": OUTCOME_COLUMNS,
    "Available N": [
        model_landmark[col].notna().sum()
        for col in OUTCOME_COLUMNS
    ],
    "Missing N": [
        model_landmark[col].isna().sum()
        for col in OUTCOME_COLUMNS
    ]
})

display(outcome_missingness)


# ------------------------------------------------------------
# 4. Exact missing-outcome patterns among excluded landmark cases
# ------------------------------------------------------------

outcome_pattern = model_landmark[OUTCOME_COLUMNS].isna().copy()

outcome_pattern["Missing pattern"] = outcome_pattern.apply(
    lambda row: (
        "Complete"
        if not row.any()
        else ", ".join(
            col
            for col in OUTCOME_COLUMNS
            if row[col]
        )
    ),
    axis=1
)

outcome_pattern_counts = (
    outcome_pattern["Missing pattern"]
    .value_counts()
    .rename_axis("Missing pattern")
    .reset_index(name="Participants")
)

display(outcome_pattern_counts)


# ------------------------------------------------------------
# 5. Participants excluded because early predictors incomplete
# ------------------------------------------------------------

early_predictor_excluded = (
    model_data.index.difference(model_landmark.index)
)

print(
    "Excluded before Week-5 landmark because of incomplete "
    "early predictor information:",
    len(early_predictor_excluded)
)

print(
    "Excluded after landmark because at least one future "
    "outcome was missing:",
    len(model_landmark) - len(model_complete)
)


# ------------------------------------------------------------
# 6. Included vs excluded baseline characteristics
# ------------------------------------------------------------

baseline_compare = model_data[
    ["age", "b_total", "sex", "treatment", "site"]
].copy()

baseline_compare["Primary analysis"] = np.where(
    baseline_compare.index.isin(model_complete.index),
    "Included",
    "Excluded"
)

continuous_comparison = (
    baseline_compare
    .groupby("Primary analysis")[["age", "b_total"]]
    .agg(["count", "mean", "std", "median"])
)

display(continuous_comparison.round(2))

for variable in ["sex", "treatment", "site"]:
    print(f"\n{variable}")
    display(
        pd.crosstab(
            baseline_compare["Primary analysis"],
            baseline_compare[variable],
            margins=True
        )
    )



# ============================================================
# SOURCE CELL In [35]:
# ============================================================
X = model_complete[ALL_FEATURES].copy()
Y = model_complete[OUTCOME_COLUMNS].copy()

participant_ids = model_complete.index.to_numpy()

print("X dimensions:", X.shape)
print("Y dimensions:", Y.shape)

display(X.head())
display(Y.head())



# ============================================================
# SOURCE CELL In [36]:
# ============================================================
outcome_summary = (
    model_complete
    .groupby("treatment")[OUTCOME_COLUMNS]
    .agg(["count", "mean", "std", "median"])
    .round(3)
)

display(outcome_summary)



# ============================================================
# SOURCE CELL In [40]:
# ============================================================
part2_qc = pd.Series({
    "All randomized participants": len(model_data),
    "Week-5 landmark participants": len(model_landmark),
    "Complete three-horizon participants": len(model_complete),
    "Numeric predictors": len(NUMERIC_FEATURES),
    "Categorical predictors": len(CATEGORICAL_FEATURES),
    "Outcomes": len(OUTCOME_COLUMNS),
    "Missing predictors in X": X.isna().sum().sum(),
    "Missing outcomes in Y": Y.isna().sum().sum()
})

display(part2_qc.to_frame("Value"))



# ============================================================
# VERIFY CORRECTED 11-COMPONENT TOTAL
# ============================================================
TOTAL_COMPONENTS = [
    "recall",
    "naming",
    "commands",
    "constructional_praxis",
    "ideational_praxis",
    "orientation",
    "word_recognition",
    "language",
    "comprehension",
    "word_finding",
    "rti"
]

model_data["calculated_baseline_total"] = (
    model_data[
        [f"b_{domain}" for domain in TOTAL_COMPONENTS]
    ]
    .sum(axis=1, min_count=len(TOTAL_COMPONENTS))
)

model_data["baseline_total_difference"] = (
    model_data["b_total"]
    - model_data["calculated_baseline_total"]
)

total_verification = model_data[
    "baseline_total_difference"
].dropna()

print(
    "Number checked:",
    len(total_verification)
)

print(
    "Maximum absolute difference:",
    total_verification.abs().max()
)

print("\nDifference frequencies:")

display(
    total_verification
    .value_counts()
    .sort_index()
    .to_frame("Records")
)



# ============================================================
# SOURCE CELL In [42]:
# ============================================================
# b_total is removed from the ridge regression model because it is
# exactly determined by the component scores.

NUMERIC_FEATURES = (
    ["age"]
    + BASELINE_DOMAIN_FEATURES
    + WEEK3_CHANGE_FEATURES
    + WEEK5_CHANGE_FEATURES
)

CATEGORICAL_FEATURES = [
    "sex",
    "treatment",
    "site"
]

ALL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

# Features for the simpler baseline-only benchmark


X = model_complete[ALL_FEATURES].copy()
Y = model_complete[OUTCOME_COLUMNS].copy()

print("Ridge regression numeric predictors:", len(NUMERIC_FEATURES))
print("Ridge regression categorical predictors:", len(CATEGORICAL_FEATURES))
print("Ridge regression total predictors:", len(ALL_FEATURES))

print("\nX dimensions:", X.shape)
print("Y dimensions:", Y.shape)



# ============================================================
# SOURCE CELL In [45]:
# ============================================================
# ============================================================
# FIGURE 2
# INDIVIDUAL ADAS-COG CHANGE TRAJECTORIES
# ============================================================

individual_trajectories = (
    model_complete[
        [
            "treatment"
        ]
        +
        OUTCOME_COLUMNS
    ]
    .reset_index()
    .melt(
        id_vars=[
            "Participant",
            "treatment"
        ],

        value_vars=
            OUTCOME_COLUMNS,

        var_name=
            "outcome",

        value_name=
            "change"
    )
)


individual_trajectories[
    "time"
] = (
    individual_trajectories[
        "outcome"
    ]
    .map({
        "y_8": 1,
        "y_16": 2,
        "y_24": 3
    })
)


baseline_trajectory_rows = (
    model_complete[
        [
            "treatment"
        ]
    ]
    .reset_index()
)

baseline_trajectory_rows[
    "outcome"
] = "baseline"

baseline_trajectory_rows[
    "change"
] = 0.0

baseline_trajectory_rows[
    "time"
] = 0


individual_trajectories = pd.concat(
    [
        baseline_trajectory_rows,
        individual_trajectories
    ],
    ignore_index=True
)


grid = sns.relplot(
    data=
        individual_trajectories,

    x=
        "time",

    y=
        "change",

    col=
        "treatment",

    col_order=[
        "R2",
        "R4",
        "S4"
    ],

    hue=
        "treatment",

    units=
        "Participant",

    estimator=
        None,

    kind=
        "line",

    marker=
        "o",

    alpha=
        0.30,

    linewidth=
        1,

    height=
        4.5,

    aspect=
        0.90,

    legend=
        False
)


for axis in grid.axes.flat:

    axis.axhline(
        0,
        linestyle="--",
        linewidth=1,
        color="black"
    )

    axis.set_xticks(
        [
            0,
            1,
            2,
            3
        ]
    )

    axis.set_xticklabels(
        [
            "Baseline",
            "8 wk",
            "16 wk",
            "24 wk"
        ]
    )

    axis.set_xlabel(
        "Assessment"
    )

    axis.set_ylabel(
        "ADAS-Cog change from baseline"
    )

    axis.grid(
        alpha=0.20
    )


grid.set_titles(
    "{col_name}"
)

grid.fig.subplots_adjust(
    top=0.83
)

grid.fig.suptitle(
    "Individual ADAS-Cog Change Trajectories by Treatment Group"
)


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    grid.fig,
    "figure2_trajectories"
)


plt.show()



# ============================================================
# SOURCE CELL In [47]:
# ============================================================
# ============================================================
# FIGURE 4
# FUTURE ADAS-COG CHANGE CORRELATIONS
# ============================================================

outcome_correlations = (
    model_complete[
        OUTCOME_COLUMNS
    ]
    .corr(
        method="spearman"
    )
)


future_correlation_labels = {
    "y_8":
        "8 weeks",

    "y_16":
        "16 weeks",

    "y_24":
        "24 weeks"
}


future_correlation_display = (
    outcome_correlations
    .rename(
        index=
            future_correlation_labels,

        columns=
            future_correlation_labels
    )
)


fig, ax = plt.subplots(
    figsize=(6.2, 5.2)
)


sns.heatmap(
    future_correlation_display,

    annot=
        True,

    fmt=
        ".2f",

    cmap=
        "vlag",

    center=
        0,

    vmin=
        -1,

    vmax=
        1,

    square=
        True,

    linewidths=
        0.5,

    cbar_kws={
        "label":
            "Spearman correlation"
    },

    ax=
        ax
)


ax.set_title(
    "Correlations Among Future ADAS-Cog Change Outcomes"
)

ax.set_xlabel(
    "Prediction horizon"
)

ax.set_ylabel(
    "Prediction horizon"
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure4_future_outcome_correlations"
)


plt.show()



# ============================================================
# SOURCE CELL In [48]:
# ============================================================
# ============================================================
# FIGURE 3
# BASELINE ADAS-COG COMPONENT CORRELATIONS
# ============================================================

baseline_domain_correlations = (
    model_complete[
        BASELINE_DOMAIN_FEATURES
    ]
    .corr(
        method="spearman"
    )
)


def domain_label(
    feature_name
):

    clean_name = (
        feature_name
        .replace(
            "b_",
            ""
        )
        .replace(
            "_",
            " "
        )
    )

    replacements = {
        "rti":
            "Remembering test instructions",

        "constructional praxis":
            "Constructional praxis",

        "ideational praxis":
            "Ideational praxis",

        "word recognition":
            "Word recognition",

        "word finding":
            "Word finding"
    }

    if clean_name in replacements:

        return replacements[
            clean_name
        ]

    return (
        clean_name.title()
    )


baseline_labels = {
    feature:
        domain_label(
            feature
        )

    for feature
    in BASELINE_DOMAIN_FEATURES
}


correlation_display = (
    baseline_domain_correlations
    .rename(
        index=
            baseline_labels,

        columns=
            baseline_labels
    )
)


fig, ax = plt.subplots(
    figsize=(10.5, 8.5)
)


sns.heatmap(
    correlation_display,

    cmap=
        "vlag",

    center=
        0,

    vmin=
        -1,

    vmax=
        1,

    square=
        True,

    linewidths=
        0.25,

    cbar_kws={
        "label":
            "Spearman correlation"
    },

    ax=
        ax
)


ax.set_title(
    "Spearman Correlations Among Baseline ADAS-Cog Components"
)

ax.set_xlabel("")
ax.set_ylabel("")


plt.setp(
    ax.get_xticklabels(),
    rotation=45,
    ha="right"
)

plt.setp(
    ax.get_yticklabels(),
    rotation=0
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure3_baseline_domain_correlations"
)


plt.show()



# ============================================================
# SOURCE CELL In [49]:
# ============================================================
numeric_feature_profile = pd.DataFrame({
    "Unique values": X[NUMERIC_FEATURES].nunique(),
    "Mean": X[NUMERIC_FEATURES].mean(),
    "Standard deviation": X[NUMERIC_FEATURES].std(),
    "Minimum": X[NUMERIC_FEATURES].min(),
    "Maximum": X[NUMERIC_FEATURES].max(),
    "Zero percentage": (
        X[NUMERIC_FEATURES]
        .eq(0)
        .mean()
        .mul(100)
    )
})

numeric_feature_profile = (
    numeric_feature_profile
    .sort_values(
        ["Standard deviation", "Zero percentage"],
        ascending=[True, False]
    )
)

display(
    numeric_feature_profile.round(3)
)



# ============================================================
# SOURCE CELL In [50]:
# ============================================================
outlier_records = []

for outcome in OUTCOME_COLUMNS:
    q1 = model_complete[outcome].quantile(0.25)
    q3 = model_complete[outcome].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    flags = model_complete[
        (model_complete[outcome] < lower_bound)
        |
        (model_complete[outcome] > upper_bound)
    ]

    for participant, row in flags.iterrows():
        outlier_records.append({
            "Participant": participant,
            "Treatment": row["treatment"],
            "Outcome": outcome,
            "Value": row[outcome],
            "Lower IQR bound": lower_bound,
            "Upper IQR bound": upper_bound
        })

outlier_table = pd.DataFrame(outlier_records)

print(
    "Number of participant-horizon outlier flags:",
    len(outlier_table)
)

display(
    outlier_table.round(3)
)



# ============================================================
# SOURCE CELL In [52]:
# ============================================================
readiness_check = pd.Series({
    "Participants": len(model_complete),
    "Predictors before encoding": len(ALL_FEATURES),
    "Numeric predictors": len(NUMERIC_FEATURES),
    "Categorical predictors": len(CATEGORICAL_FEATURES),
    "Outcomes": len(OUTCOME_COLUMNS),
    "Missing X values": X.isna().sum().sum(),
    "Missing Y values": Y.isna().sum().sum(),
    "Constant numeric predictors":
        (X[NUMERIC_FEATURES].nunique() <= 1).sum(),
    "Duplicated participants":
        model_complete.index.duplicated().sum()
})

display(
    readiness_check.to_frame("Value")
)

assert X.isna().sum().sum() == 0
assert Y.isna().sum().sum() == 0
assert model_complete.index.duplicated().sum() == 0

print("\nData are ready for participant-level model validation.")



# ============================================================
# SOURCE CELL In [54]:
# ============================================================
from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    StratifiedKFold,
    GridSearchCV
)

from sklearn.preprocessing import (
    StandardScaler,
    OneHotEncoder
)

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score
)

from sklearn.base import clone

print("Modelling functions imported.")



# ============================================================
# SOURCE CELL In [55]:
# ============================================================
X = model_complete[ALL_FEATURES].copy()
Y = model_complete[OUTCOME_COLUMNS].copy()

print("Participants:", len(X))
print("Predictors:", X.shape[1])
print("Outcomes:", Y.shape[1])

print("\nTreatment groups:")
display(
    model_complete["treatment"]
    .value_counts()
    .sort_index()
    .to_frame("Participants")
)

print("\nSites:")
display(
    model_complete["site"]
    .value_counts()
    .sort_index()
    .to_frame("Participants")
)

assert X.index.equals(Y.index)
assert X.isna().sum().sum() == 0
assert Y.isna().sum().sum() == 0



# ============================================================
# SOURCE CELL In [56]:
# ============================================================
model_strata = (
    model_complete["treatment"].astype(str)
    + "_"
    + model_complete["site"].astype(str)
)

stratum_counts = (
    model_strata
    .value_counts()
    .sort_index()
)

display(
    stratum_counts.to_frame("Participants")
)

if stratum_counts.min() < 5:
    print(
        "At least one treatment-site stratum has fewer than "
        "five participants. Using treatment-only stratification."
    )

    model_strata = (
        model_complete["treatment"]
        .astype(str)
    )
else:
    print(
        "Treatment-site stratification can be used."
    )



# ============================================================
# SOURCE CELL In [57]:
# ============================================================
N_SPLITS = 5
N_REPEATS = 5

outer_cv = RepeatedStratifiedKFold(
    n_splits=N_SPLITS,
    n_repeats=N_REPEATS,
    random_state=RANDOM_STATE
)

outer_splits = list(
    outer_cv.split(
        X,
        model_strata
    )
)

print("Total outer splits:", len(outer_splits))
print(
    "Expected:",
    N_SPLITS * N_REPEATS
)



# ============================================================
# SOURCE CELL In [58]:
# ============================================================
fold_audit_records = []

for split_number, (train_indices, test_indices) in enumerate(
    outer_splits
):
    repeat_number = split_number // N_SPLITS + 1
    fold_number = split_number % N_SPLITS + 1

    train_participants = X.index[train_indices]
    test_participants = X.index[test_indices]

    overlap = set(train_participants).intersection(
        set(test_participants)
    )

    fold_audit_records.append({
        "Repeat": repeat_number,
        "Fold": fold_number,
        "Training N": len(train_indices),
        "Testing N": len(test_indices),
        "Participant overlap": len(overlap),
        "Test R2": (
            model_complete.iloc[test_indices]["treatment"]
            .eq("R2")
            .sum()
        ),
        "Test R4": (
            model_complete.iloc[test_indices]["treatment"]
            .eq("R4")
            .sum()
        ),
        "Test S4": (
            model_complete.iloc[test_indices]["treatment"]
            .eq("S4")
            .sum()
        ),
        "Test MB": (
            model_complete.iloc[test_indices]["site"]
            .eq("MB")
            .sum()
        ),
        "Test MQ": (
            model_complete.iloc[test_indices]["site"]
            .eq("MQ")
            .sum()
        )
    })

fold_audit = pd.DataFrame(fold_audit_records)

display(fold_audit)

assert fold_audit["Participant overlap"].max() == 0



# ============================================================
# SOURCE CELL In [59]:
# ============================================================
test_frequency = pd.DataFrame(
    0,
    index=X.index,
    columns=[
        f"Repeat_{repeat_number}"
        for repeat_number in range(1, N_REPEATS + 1)
    ]
)

for split_number, (_, test_indices) in enumerate(
    outer_splits
):
    repeat_number = split_number // N_SPLITS + 1

    test_frequency.iloc[
        test_indices,
        repeat_number - 1
    ] += 1

frequency_summary = (
    test_frequency
    .apply(pd.Series.value_counts)
    .fillna(0)
    .astype(int)
)

display(frequency_summary)

assert (test_frequency == 1).all().all()

print(
    "Every participant appears once in the test set "
    "within each repetition."
)



# ============================================================
# SOURCE CELL In [60]:
# ============================================================
# ============================================================
# PREPROCESSING
# Primary modelling sample contains no missing predictors,
# so imputation is not required.
# ============================================================

numeric_preprocessing = Pipeline(
    steps=[
        (
            "scaler",
            StandardScaler()
        )
    ]
)

categorical_preprocessing = Pipeline(
    steps=[
        (
            "encoder",
            OneHotEncoder(
                drop="first",
                handle_unknown="ignore",
                sparse_output=False
            )
        )
    ]
)

domain_preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_preprocessing,
            NUMERIC_FEATURES
        ),
        (
            "categorical",
            categorical_preprocessing,
            CATEGORICAL_FEATURES
        )
    ],
    remainder="drop"
)

print("Preprocessing pipeline created without imputation.")



# ============================================================
# SOURCE CELL In [61]:
# ============================================================
# ============================================================
# ENCODED FEATURE COUNT AND REFERENCE CATEGORIES
# ============================================================

preprocessor_audit = clone(domain_preprocessor)

preprocessor_audit.fit(
    model_complete[ALL_FEATURES]
)

transformed_feature_names = (
    preprocessor_audit.get_feature_names_out()
)

print(
    "Predictors before encoding:",
    len(ALL_FEATURES)
)

print(
    "Columns after preprocessing/encoding:",
    len(transformed_feature_names)
)

print("\nEncoded feature names:")
for feature in transformed_feature_names:
    print(feature)


# Reference categories from drop="first"
fitted_encoder = (
    preprocessor_audit
    .named_transformers_["categorical"]
    .named_steps["encoder"]
)

reference_records = []

for variable, categories, dropped_index in zip(
    CATEGORICAL_FEATURES,
    fitted_encoder.categories_,
    fitted_encoder.drop_idx_
):
    reference_records.append({
        "Variable": variable,
        "Categories": list(categories),
        "Reference category": categories[dropped_index]
    })

reference_categories = pd.DataFrame(reference_records)

display(reference_categories)



# ============================================================
# SOURCE CELL In [62]:
# ============================================================
n_participants = len(model_complete)
n_outcomes = len(OUTCOME_COLUMNS)

Y_array = Y.to_numpy(dtype=float)

benchmark_names = [
    "No change",
    "Training mean"
]

benchmark_predictions = {
    benchmark: np.full(
        (
            N_REPEATS,
            n_participants,
            n_outcomes
        ),
        np.nan
    )
    for benchmark in benchmark_names
}

for split_number, (train_indices, test_indices) in enumerate(
    outer_splits
):
    repeat_index = split_number // N_SPLITS

    Y_train = Y_array[train_indices]

    no_change_prediction = np.zeros(
        (len(test_indices), n_outcomes)
    )

    training_mean = Y_train.mean(axis=0)

    training_mean_prediction = np.tile(
        training_mean,
        (len(test_indices), 1)
    )

    benchmark_predictions[
        "No change"
    ][repeat_index, test_indices, :] = no_change_prediction

    benchmark_predictions[
        "Training mean"
    ][repeat_index, test_indices, :] = (
        training_mean_prediction
    )

for benchmark, predictions in benchmark_predictions.items():
    assert not np.isnan(predictions).any()

print("All benchmark out-of-fold predictions created.")



# ============================================================
# SOURCE CELL In [63]:
# ============================================================
def calculate_repeated_metrics(
    observed,
    repeated_predictions,
    model_name,
    outcome_names
):
    records = []

    for repeat_index in range(
        repeated_predictions.shape[0]
    ):
        predicted = repeated_predictions[repeat_index]

        for outcome_index, outcome in enumerate(
            outcome_names
        ):
            observed_horizon = observed[:, outcome_index]
            predicted_horizon = predicted[:, outcome_index]

            records.append({
                "Model": model_name,
                "Repeat": repeat_index + 1,
                "Horizon": outcome,
                "MAE": mean_absolute_error(
                    observed_horizon,
                    predicted_horizon
                ),
                "RMSE": root_mean_squared_error(
                    observed_horizon,
                    predicted_horizon
                ),
                "R2": r2_score(
                    observed_horizon,
                    predicted_horizon
                )
            })

        records.append({
            "Model": model_name,
            "Repeat": repeat_index + 1,
            "Horizon": "Overall",
            "MAE": mean_absolute_error(
                observed,
                predicted
            ),
            "RMSE": root_mean_squared_error(
                observed,
                predicted
            ),
            "R2": r2_score(
                observed,
                predicted,
                multioutput="variance_weighted"
            )
        })

    return pd.DataFrame(records)



# ============================================================
# SOURCE CELL In [64]:
# ============================================================
benchmark_metric_tables = []

for benchmark_name, predictions in (
    benchmark_predictions.items()
):
    benchmark_metric_tables.append(
        calculate_repeated_metrics(
            observed=Y_array,
            repeated_predictions=predictions,
            model_name=benchmark_name,
            outcome_names=OUTCOME_COLUMNS
        )
    )

benchmark_metrics = pd.concat(
    benchmark_metric_tables,
    ignore_index=True
)

display(
    benchmark_metrics.head(12)
)



# ============================================================
# SOURCE CELL In [65]:
# ============================================================
benchmark_summary = (
    benchmark_metrics
    .groupby(["Model", "Horizon"])
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
    .round(3)
)

display(benchmark_summary)



# ============================================================
# SOURCE CELL In [68]:
# ============================================================
validation_configuration = {
    "participants": len(model_complete),
    "outer_folds": N_SPLITS,
    "outer_repeats": N_REPEATS,
    "total_outer_splits": len(outer_splits),
    "random_state": RANDOM_STATE,
    "stratification": (
        "treatment and site"
        if "_" in model_strata.iloc[0]
        else "treatment only"
    ),
    "outcomes": OUTCOME_COLUMNS,
    "predictor_count": len(ALL_FEATURES)
}

display(
    pd.Series(
        validation_configuration
    ).to_frame("Value")
)



# ============================================================
# SOURCE CELL In [69]:
# ============================================================
#model fitting
required_part5_objects = [
    "model_complete",
    "model_strata",
    "outer_splits",
    "domain_preprocessor",
    "benchmark_metrics",
    "benchmark_predictions",
    "calculate_repeated_metrics",
    "ALL_FEATURES",
    "OUTCOME_COLUMNS",
    "N_SPLITS",
    "N_REPEATS"
]

missing_objects = [
    object_name
    for object_name in required_part5_objects
    if object_name not in globals()
]

if missing_objects:
    raise RuntimeError(
        "Run Parts 1–4 first. Missing objects: "
        + ", ".join(missing_objects)
    )

print("All Part 5 prerequisites are available.")



# ============================================================
# SOURCE CELL In [70]:
# ============================================================
from sklearn.linear_model import (
    Ridge,
    MultiTaskElasticNet
)

from sklearn.ensemble import RandomForestRegressor

from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    StratifiedKFold
)

from sklearn.base import clone

import time
import warnings

print("Part 5 modelling functions imported.")



# ============================================================
# SOURCE CELL In [71]:
# ============================================================
MODEL_INPUT_FEATURES = list(ALL_FEATURES)

X_model_input = model_complete[
    MODEL_INPUT_FEATURES
].copy()

Y_model = model_complete[
    OUTCOME_COLUMNS
].copy()

Y_array = Y_model.to_numpy(dtype=float)

print(
    "Common model-input dimensions:",
    X_model_input.shape
)

print(
    "Outcome dimensions:",
    Y_model.shape
)

assert X_model_input.index.equals(Y_model.index)
assert X_model_input.isna().sum().sum() == 0
assert Y_model.isna().sum().sum() == 0



# ============================================================
# SOURCE CELL In [72]:
# ============================================================
RIDGE_ALPHA_GRID = [
    0.01,
    0.1,
    1.0,
    10.0,
    100.0,
    1000.0
]

ELASTIC_ALPHA_GRID = [
    0.003,
    0.01,
    0.03,
    0.1,
    0.3,
    1.0
]

ELASTIC_L1_GRID = [
    0.1,
    0.5,
    0.9
]



# ============================================================
# SOURCE CELL In [73]:
# ============================================================
def make_model_search(
    model_name,
    inner_splits,
    split_seed
):
    if model_name == "Ridge regression":
        pipeline = Pipeline(
            steps=[
                (
                    "preprocess",
                    clone(domain_preprocessor)
                ),
                (
                    "model",
                    Ridge()
                )
            ]
        )

        return GridSearchCV(
            estimator=pipeline,
            param_grid={
                "model__alpha": RIDGE_ALPHA_GRID
            },
            scoring="neg_mean_absolute_error",
            cv=inner_splits,
            refit=True,
            n_jobs=N_JOBS,
            return_train_score=False,
            error_score="raise"
        )

    if model_name == "Multi-task elastic net":
        pipeline = Pipeline(
            steps=[
                (
                    "preprocess",
                    clone(domain_preprocessor)
                ),
                (
                    "model",
                    MultiTaskElasticNet(
                        max_iter=50000,
                        tol=1e-4,
                        selection="cyclic"
                    )
                )
            ]
        )

        return GridSearchCV(
            estimator=pipeline,
            param_grid={
                "model__alpha": ELASTIC_ALPHA_GRID,
                "model__l1_ratio": ELASTIC_L1_GRID
            },
            scoring="neg_mean_absolute_error",
            cv=inner_splits,
            refit=True,
            n_jobs=N_JOBS,
            return_train_score=False,
            error_score="raise"
        )

    if model_name == "Restricted random forest":
        pipeline = Pipeline(
            steps=[
                (
                    "preprocess",
                    clone(domain_preprocessor)
                ),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=200,
                        random_state=split_seed,
                        n_jobs=1
                    )
                )
            ]
        )

        parameter_distributions = {
            "model__max_depth": [
                2,
                3,
                4,
                5,
                None
            ],
            "model__min_samples_leaf": [
                2,
                3,
                5,
                8,
                10
            ],
            "model__min_samples_split": [
                2,
                5,
                10
            ],
            "model__max_features": [
                0.3,
                0.5,
                0.8,
                1.0
            ]
        }

        return RandomizedSearchCV(
            estimator=pipeline,
            param_distributions=parameter_distributions,
            n_iter=12,
            scoring="neg_mean_absolute_error",
            cv=inner_splits,
            refit=True,
            n_jobs=N_JOBS,
            random_state=split_seed,
            return_train_score=False,
            error_score="raise"
        )

    raise ValueError(
        f"Unknown model: {model_name}"
    )



# ============================================================
# SOURCE CELL In [74]:
# ============================================================
SUPERVISED_MODEL_NAMES = [
    "Ridge regression",
    "Multi-task elastic net",
    "Restricted random forest"
]

n_participants = len(model_complete)
n_outcomes = len(OUTCOME_COLUMNS)

supervised_predictions = {
    model_name: np.full(
        (
            N_REPEATS,
            n_participants,
            n_outcomes
        ),
        np.nan
    )
    for model_name in SUPERVISED_MODEL_NAMES
}

best_parameter_records = []

print("Prediction storage initialized.")



# ============================================================
# SOURCE CELL In [75]:
# ============================================================
fitting_start_time = time.time()

for split_number, (train_indices, test_indices) in enumerate(
    outer_splits
):
    repeat_index = split_number // N_SPLITS
    fold_index = split_number % N_SPLITS

    split_seed = (
        RANDOM_STATE
        + split_number
        + 1
    )

    X_train = X_model_input.iloc[train_indices]
    X_test = X_model_input.iloc[test_indices]

    Y_train = Y_model.iloc[train_indices]

    training_strata = model_strata.iloc[
        train_indices
    ]

    inner_cv = StratifiedKFold(
        n_splits=3,
        shuffle=True,
        random_state=split_seed
    )

    inner_splits = list(
        inner_cv.split(
            X_train,
            training_strata
        )
    )

    print(
        f"\nOuter split {split_number + 1:02d}/"
        f"{len(outer_splits)} "
        f"(repeat {repeat_index + 1}, "
        f"fold {fold_index + 1})"
    )

    for model_name in SUPERVISED_MODEL_NAMES:
        search = make_model_search(
            model_name=model_name,
            inner_splits=inner_splits,
            split_seed=split_seed
        )

        with warnings.catch_warnings():
            warnings.simplefilter("once")

            search.fit(
                X_train,
                Y_train
            )

        test_prediction = search.predict(
            X_test
        )

        supervised_predictions[
            model_name
        ][
            repeat_index,
            test_indices,
            :
        ] = test_prediction

        best_parameter_records.append({
            "Model": model_name,
            "Repeat": repeat_index + 1,
            "Fold": fold_index + 1,
            "Outer split": split_number + 1,
            "Training N": len(train_indices),
            "Testing N": len(test_indices),
            "Best inner MAE":
                -search.best_score_,
            "Best parameters":
                search.best_params_
        })

        print(
            f"  {model_name}: "
            f"inner MAE = {-search.best_score_:.3f}"
        )

fitting_elapsed_seconds = (
    time.time()
    - fitting_start_time
)

print("\nNested model fitting completed.")
print(
    "Elapsed minutes:",
    round(fitting_elapsed_seconds / 60, 2)
)



# ============================================================
# SOURCE CELL In [76]:
# ============================================================
prediction_verification = []

for model_name, predictions in (
    supervised_predictions.items()
):
    missing_predictions = np.isnan(
        predictions
    ).sum()

    prediction_verification.append({
        "Model": model_name,
        "Prediction array shape":
            str(predictions.shape),
        "Missing prediction values":
            missing_predictions
    })

prediction_verification = pd.DataFrame(
    prediction_verification
)

display(prediction_verification)

assert (
    prediction_verification[
        "Missing prediction values"
    ].max()
    == 0
)

print(
    "Every model produced an out-of-fold prediction "
    "for every participant in every repetition."
)



# ============================================================
# SOURCE CELL In [77]:
# ============================================================
supervised_metric_tables = []

for model_name, predictions in (
    supervised_predictions.items()
):
    model_metrics = calculate_repeated_metrics(
        observed=Y_array,
        repeated_predictions=predictions,
        model_name=model_name,
        outcome_names=OUTCOME_COLUMNS
    )

    supervised_metric_tables.append(
        model_metrics
    )

supervised_metrics = pd.concat(
    supervised_metric_tables,
    ignore_index=True
)

display(
    supervised_metrics.head(12)
)



# ============================================================
# SOURCE CELL In [78]:
# ============================================================
all_model_metrics = pd.concat(
    [
        benchmark_metrics,
        supervised_metrics
    ],
    ignore_index=True
)

all_model_predictions = {
    **benchmark_predictions,
    **supervised_predictions
}

MODEL_COMPARISON_ORDER = [
    "Ridge regression",
    "Multi-task elastic net",
    "Restricted random forest"
]

comparison_metrics = all_model_metrics.loc[
    all_model_metrics["Model"].isin(
        MODEL_COMPARISON_ORDER
    )
].copy()

comparison_summary = (
    comparison_metrics
    .groupby(["Model", "Horizon"])
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
)

horizon_order = [
    "y_8",
    "y_16",
    "y_24",
    "Overall"
]

comparison_summary["Horizon"] = pd.Categorical(
    comparison_summary["Horizon"],
    categories=horizon_order,
    ordered=True
)

comparison_summary["Model"] = pd.Categorical(
    comparison_summary["Model"],
    categories=MODEL_COMPARISON_ORDER,
    ordered=True
)

comparison_summary = (
    comparison_summary
    .sort_values(["Horizon", "Model"])
    .reset_index(drop=True)
)

display(
    comparison_summary.round(3)
)



# ============================================================
# SOURCE CELL In [79]:
# ============================================================
# ============================================================
# SUPERVISOR REVISION:
# FAIR NESTED RIDGE COMPARATOR MODELS
#
# A = baseline demographics + baseline total
# B = A + treatment + site
# C = B + early TOTAL-score response
# D = B + early DOMAIN-specific response
#
# IMPORTANT:
# C and D contain the SAME baseline/trial information.
#
# C represents early cognitive response using:
#   d3_total + d5_total
#
# D represents early cognitive response using:
#   11 Week-3 domain changes + 11 Week-5 domain changes
#
# D deliberately DOES NOT include:
#   - d3_total
#   - d5_total
#   - baseline domain scores
#
# This makes C vs D a direct test of whether the detailed
# pattern of early domain response improves prediction beyond
# the simpler overall early ADAS-Cog total-score response.
#
# Same participants and SAME outer CV splits are used.
# ============================================================

from sklearn.linear_model import Ridge
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, StratifiedKFold


# ============================================================
# MAKE SURE TOTAL-SCORE EARLY CHANGES EXIST
# ============================================================

if "d3_total" not in model_complete.columns:
    model_complete["d3_total"] = (
        model_complete["w3_total"]
        - model_complete["b_total"]
    )

if "d5_total" not in model_complete.columns:
    model_complete["d5_total"] = (
        model_complete["w5_total"]
        - model_complete["b_total"]
    )


# ============================================================
# DEFINE FAIR COMPARATOR FEATURE SETS
# ============================================================

COMPARATOR_FEATURES = {

    # --------------------------------------------------------
    # MODEL A:
    # Baseline demographic + baseline cognitive status
    # --------------------------------------------------------
    "A: Baseline": [
        "age",
        "sex",
        "b_total"
    ],

    # --------------------------------------------------------
    # MODEL B:
    # Baseline model + trial design variables
    # --------------------------------------------------------
    "B: Baseline + trial": [
        "age",
        "sex",
        "b_total",
        "treatment",
        "site"
    ],

    # --------------------------------------------------------
    # MODEL C:
    # Baseline/trial variables + EARLY TOTAL-SCORE RESPONSE
    # --------------------------------------------------------
    "C: Early total response": [
        "age",
        "sex",
        "b_total",
        "treatment",
        "site",
        "d3_total",
        "d5_total"
    ],

    # --------------------------------------------------------
    # MODEL D:
    # SAME baseline/trial variables as Model C
    # but replace total-score changes with individual
    # domain-specific Week-3 and Week-5 changes.
    #
    # DO NOT add:
    #   d3_total
    #   d5_total
    #   baseline domain scores
    # --------------------------------------------------------
    "D: Domain-specific response": (
        [
            "age",
            "sex",
            "b_total",
            "treatment",
            "site"
        ]
        + WEEK3_CHANGE_FEATURES
        + WEEK5_CHANGE_FEATURES
    )
}


# ============================================================
# VERIFY FEATURE COUNTS
# ============================================================

print("FAIR COMPARATOR FEATURE SETS")
print("=" * 60)

for model_name, feature_columns in COMPARATOR_FEATURES.items():
    print(
        f"{model_name}: "
        f"{len(feature_columns)} predictors"
    )

print("\nExpected:")
print("A = 3 predictors")
print("B = 5 predictors")
print("C = 7 predictors")
print("D = 27 predictors")


# ============================================================
# VERIFY THAT C AND D SHARE IDENTICAL BASE/TRIAL INFORMATION
# ============================================================

COMMON_BASE_FEATURES = [
    "age",
    "sex",
    "b_total",
    "treatment",
    "site"
]

assert all(
    feature in COMPARATOR_FEATURES["C: Early total response"]
    for feature in COMMON_BASE_FEATURES
)

assert all(
    feature in COMPARATOR_FEATURES["D: Domain-specific response"]
    for feature in COMMON_BASE_FEATURES
)

# Model D must NOT contain total-score response variables
assert "d3_total" not in COMPARATOR_FEATURES[
    "D: Domain-specific response"
]

assert "d5_total" not in COMPARATOR_FEATURES[
    "D: Domain-specific response"
]

# Model D must NOT contain baseline domain variables
assert not any(
    feature in COMPARATOR_FEATURES[
        "D: Domain-specific response"
    ]
    for feature in BASELINE_DOMAIN_FEATURES
)

print("\nComparator structure verified successfully.")


# ============================================================
# PREPROCESSOR FOR EACH COMPARATOR MODEL
# ============================================================

def make_comparator_preprocessor(feature_columns):

    categorical_columns = [
        col
        for col in [
            "sex",
            "treatment",
            "site"
        ]
        if col in feature_columns
    ]

    numeric_columns = [
        col
        for col in feature_columns
        if col not in categorical_columns
    ]

    transformers = []

    if numeric_columns:
        transformers.append(
            (
                "numeric",
                StandardScaler(),
                numeric_columns
            )
        )

    if categorical_columns:
        transformers.append(
            (
                "categorical",
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                categorical_columns
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


# ============================================================
# FUNCTION:
# RUN NESTED RIDGE USING SAME PARTICIPANTS AND OUTER SPLITS
# ============================================================

def run_nested_ridge_same_sample(
    data,
    feature_columns,
    outcome_columns
):

    # --------------------------------------------------------
    # IMPORTANT:
    # outer_splits were created using model_complete.
    # Therefore participant order must remain identical.
    # --------------------------------------------------------

    if not data.index.equals(model_complete.index):
        raise ValueError(
            "This function requires the same participant order "
            "as model_complete."
        )

    X_local = data[
        feature_columns
    ].copy()

    Y_local = data[
        outcome_columns
    ].copy()

    # --------------------------------------------------------
    # NO MISSING VALUES ALLOWED IN THIS COMPLETE-CASE ANALYSIS
    # --------------------------------------------------------

    assert (
        X_local
        .isna()
        .sum()
        .sum()
        == 0
    )

    assert (
        Y_local
        .isna()
        .sum()
        .sum()
        == 0
    )

    # --------------------------------------------------------
    # STORAGE FOR REPEATED OUT-OF-FOLD PREDICTIONS
    #
    # shape:
    # repeats × participants × outcomes
    # --------------------------------------------------------

    predictions = np.full(
        (
            N_REPEATS,
            len(data),
            len(outcome_columns)
        ),
        np.nan
    )

    parameter_records = []

    # ========================================================
    # OUTER CROSS-VALIDATION
    # ========================================================

    for split_number, (
        train_indices,
        test_indices
    ) in enumerate(outer_splits):

        repeat_index = (
            split_number // N_SPLITS
        )

        X_train = X_local.iloc[
            train_indices
        ]

        X_test = X_local.iloc[
            test_indices
        ]

        Y_train = Y_local.iloc[
            train_indices
        ]

        # ----------------------------------------------------
        # SAME treatment-site strata used in primary analysis
        # ----------------------------------------------------

        training_strata = (
            model_strata
            .iloc[train_indices]
        )

        # ----------------------------------------------------
        # INNER 3-FOLD STRATIFIED CV
        # ----------------------------------------------------

        inner_cv = StratifiedKFold(
            n_splits=3,
            shuffle=True,
            random_state=(
                RANDOM_STATE
                + split_number
                + 1
            )
        )

        inner_splits = list(
            inner_cv.split(
                X_train,
                training_strata
            )
        )

        # ----------------------------------------------------
        # PREPROCESSING + RIDGE PIPELINE
        # ----------------------------------------------------

        pipeline = Pipeline(
            steps=[
                (
                    "preprocess",
                    make_comparator_preprocessor(
                        feature_columns
                    )
                ),
                (
                    "model",
                    Ridge(
                        fit_intercept=True
                    )
                )
            ]
        )

        # ----------------------------------------------------
        # INNER-CV HYPERPARAMETER SELECTION
        #
        # neg_mean_absolute_error averages MAE equally across
        # the three outcome columns.
        # ----------------------------------------------------

        search = GridSearchCV(
            estimator=pipeline,

            param_grid={
                "model__alpha":
                    RIDGE_ALPHA_GRID
            },

            scoring="neg_mean_absolute_error",

            cv=inner_splits,

            refit=True,

            n_jobs=N_JOBS,

            error_score="raise"
        )

        # ----------------------------------------------------
        # FIT ONLY ON OUTER TRAINING PARTICIPANTS
        # ----------------------------------------------------

        search.fit(
            X_train,
            Y_train
        )

        # ----------------------------------------------------
        # PREDICT HELD-OUT OUTER TEST PARTICIPANTS
        # ----------------------------------------------------

        predictions[
            repeat_index,
            test_indices,
            :
        ] = search.predict(
            X_test
        )

        # ----------------------------------------------------
        # STORE SELECTED RIDGE ALPHA
        # ----------------------------------------------------

        parameter_records.append({
            "Outer split":
                split_number + 1,

            "Repeat":
                repeat_index + 1,

            "Best alpha":
                search.best_params_[
                    "model__alpha"
                ]
        })

    # --------------------------------------------------------
    # VERIFY EVERY PARTICIPANT RECEIVED AN OOF PREDICTION
    # IN EVERY REPEAT
    # --------------------------------------------------------

    assert not np.isnan(
        predictions
    ).any()

    return (
        predictions,
        pd.DataFrame(
            parameter_records
        )
    )



# ============================================================
# SOURCE CELL In [80]:
# ============================================================
# ============================================================
# FIT ALL FOUR COMPARATOR MODELS
# ============================================================

comparator_predictions = {}
comparator_parameters = {}
comparator_metric_tables = []

Y_comparator = (
    model_complete[OUTCOME_COLUMNS]
    .to_numpy(dtype=float)
)

for model_name, features in (
    COMPARATOR_FEATURES.items()
):

    print("\nRunning:", model_name)
    print("Predictors:", len(features))

    predictions, parameters = (
        run_nested_ridge_same_sample(
            data=model_complete,
            feature_columns=features,
            outcome_columns=OUTCOME_COLUMNS
        )
    )

    comparator_predictions[
        model_name
    ] = predictions

    comparator_parameters[
        model_name
    ] = parameters

    comparator_metric_tables.append(
        calculate_repeated_metrics(
            observed=Y_comparator,
            repeated_predictions=predictions,
            model_name=model_name,
            outcome_names=OUTCOME_COLUMNS
        )
    )


comparator_metrics = pd.concat(
    comparator_metric_tables,
    ignore_index=True
)

comparator_summary = (
    comparator_metrics
    .groupby(
        ["Model", "Horizon"]
    )
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
    .round(3)
)

display(comparator_summary)



# ============================================================
# SOURCE CELL In [81]:
# ============================================================
# ============================================================
# INCREMENTAL VALUE OF DOMAIN-SPECIFIC INFORMATION
# MODEL C VERSUS MODEL D
# ============================================================

comparator_wide = (
    comparator_metrics
    .pivot_table(
        index=["Repeat", "Horizon"],
        columns="Model",
        values=["MAE", "RMSE", "R2"]
    )
)

incremental_domain_value = pd.DataFrame({
    "MAE improvement C minus D":
        (
            comparator_wide["MAE"][
                "C: Early total response"
            ]
            -
            comparator_wide["MAE"][
                "D: Domain-specific response"
            ]
        ),

    "RMSE improvement C minus D":
        (
            comparator_wide["RMSE"][
                "C: Early total response"
            ]
            -
            comparator_wide["RMSE"][
                "D: Domain-specific response"
            ]
        ),

    "R2 improvement D minus C":
        (
            comparator_wide["R2"][
                "D: Domain-specific response"
            ]
            -
            comparator_wide["R2"][
                "C: Early total response"
            ]
        )
}).reset_index()


incremental_summary = (
    incremental_domain_value
    .groupby("Horizon")
    .agg(
        MAE_gain_mean=(
            "MAE improvement C minus D",
            "mean"
        ),
        MAE_gain_sd=(
            "MAE improvement C minus D",
            "std"
        ),
        RMSE_gain_mean=(
            "RMSE improvement C minus D",
            "mean"
        ),
        R2_gain_mean=(
            "R2 improvement D minus C",
            "mean"
        )
    )
    .reset_index()
    .round(4)
)

display(incremental_summary)

print(
    "\nPositive MAE/RMSE gain means the "
    "domain-specific model had lower error."
)

print(
    "Positive R2 gain means the "
    "domain-specific model explained more variance."
)



# ============================================================
# SOURCE CELL In [82]:
# ============================================================
# ============================================================
# SENSITIVITY:
# ABSOLUTE FOLLOW-UP ADAS-COG AS THE OUTCOME
#
# This avoids having baseline total appear on both
# sides of the change-score equation.
# ============================================================

ABSOLUTE_OUTCOMES = [
    "f8_total",
    "f16_total",
    "f24_total"
]

absolute_predictions, absolute_parameters = (
    run_nested_ridge_same_sample(
        data=model_complete,
        feature_columns=COMPARATOR_FEATURES[
            "D: Domain-specific response"
        ],
        outcome_columns=ABSOLUTE_OUTCOMES
    )
)

Y_absolute = (
    model_complete[ABSOLUTE_OUTCOMES]
    .to_numpy(dtype=float)
)

absolute_metrics = (
    calculate_repeated_metrics(
        observed=Y_absolute,
        repeated_predictions=absolute_predictions,
        model_name=(
            "Domain model: absolute follow-up outcome"
        ),
        outcome_names=ABSOLUTE_OUTCOMES
    )
)

absolute_summary = (
    absolute_metrics
    .groupby("Horizon")
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
    .round(3)
)

display(absolute_summary)



# ============================================================
# SOURCE CELL In [83]:
# ============================================================
# ============================================================
# SENSITIVITY:
# REMOVE ALL WEEK-3 RESPONSE INFORMATION
# ============================================================

DOMAIN_NO_WEEK3_FEATURES = (
    [
        "age",
        "sex",
        "b_total",
        "treatment",
        "site",
        "d5_total"
    ]
    + BASELINE_DOMAIN_FEATURES
    + WEEK5_CHANGE_FEATURES
)

print("Predictors in no-Week-3 model:")
print(DOMAIN_NO_WEEK3_FEATURES)
print("\nNumber of predictors:", len(DOMAIN_NO_WEEK3_FEATURES))


no_week3_predictions, no_week3_parameters = (
    run_nested_ridge_same_sample(
        data=model_complete,
        feature_columns=DOMAIN_NO_WEEK3_FEATURES,
        outcome_columns=OUTCOME_COLUMNS
    )
)

no_week3_metrics = (
    calculate_repeated_metrics(
        observed=Y_comparator,
        repeated_predictions=no_week3_predictions,
        model_name="Domain model without Week 3",
        outcome_names=OUTCOME_COLUMNS
    )
)

week3_sensitivity_metrics = pd.concat(
    [
        comparator_metrics.loc[
            comparator_metrics["Model"]
            == "D: Domain-specific response"
        ],
        no_week3_metrics
    ],
    ignore_index=True
)

week3_sensitivity_summary = (
    week3_sensitivity_metrics
    .groupby(
        ["Model", "Horizon"]
    )
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
    .round(3)
)

display(week3_sensitivity_summary)



# ============================================================
# SOURCE CELL In [84]:
# ============================================================
# ============================================================
# FIGURE 5
# PREDICTOR-SET COMPARISON
#
# A = Baseline only
# B = Baseline + trial
# C = Early total response
# D = Early domain response
# ============================================================

predictor_plot_data = (
    comparator_metrics.copy()
)


predictor_plot_data[
    "Horizon label"
] = (
    predictor_plot_data[
        "Horizon"
    ]
    .map(
        HORIZON_LABELS
    )
)


PREDICTOR_MODEL_LABELS = {
    "A: Baseline":
        "A: Baseline",

    "B: Baseline + trial":
        "B: Baseline + trial",

    "C: Early total response":
        "C: Early total response",

    "D: Domain-specific response":
        "D: Early domain response"
}


predictor_plot_data[
    "Model label"
] = (
    predictor_plot_data[
        "Model"
    ]
    .map(
        PREDICTOR_MODEL_LABELS
    )
)


predictor_plot_data[
    "Horizon label"
] = pd.Categorical(
    predictor_plot_data[
        "Horizon label"
    ],

    categories=
        HORIZON_ORDER,

    ordered=
        True
)


predictor_model_order = [
    "A: Baseline",
    "B: Baseline + trial",
    "C: Early total response",
    "D: Early domain response"
]


fig, axes = plt.subplots(
    1,
    2,
    figsize=(15, 5.5)
)


# ------------------------------------------------------------
# A. MAE
# ------------------------------------------------------------

sns.barplot(
    data=
        predictor_plot_data,

    x=
        "Horizon label",

    y=
        "MAE",

    hue=
        "Model label",

    hue_order=
        predictor_model_order,

    errorbar=
        "sd",

    capsize=
        0.10,

    ax=
        axes[0]
)


axes[0].set_title(
    "A. Mean Absolute Error"
)

axes[0].set_xlabel(
    "Prediction horizon"
)

axes[0].set_ylabel(
    "Mean absolute error"
)

axes[0].grid(
    axis="y",
    alpha=0.20
)


# ------------------------------------------------------------
# B. R-SQUARED
# ------------------------------------------------------------

sns.barplot(
    data=
        predictor_plot_data,

    x=
        "Horizon label",

    y=
        "R2",

    hue=
        "Model label",

    hue_order=
        predictor_model_order,

    errorbar=
        "sd",

    capsize=
        0.10,

    ax=
        axes[1]
)


axes[1].axhline(
    0,
    linestyle="--",
    linewidth=1,
    color="black"
)

axes[1].set_title(
    "B. Out-of-Sample $R^2$"
)

axes[1].set_xlabel(
    "Prediction horizon"
)

axes[1].set_ylabel(
    "Out-of-sample $R^2$"
)

axes[1].grid(
    axis="y",
    alpha=0.20
)


# ------------------------------------------------------------
# COMMON LEGEND
# ------------------------------------------------------------

if axes[1].legend_ is not None:
    axes[1].legend_.remove()


handles, labels = (
    axes[0]
    .get_legend_handles_labels()
)


if axes[0].legend_ is not None:
    axes[0].legend_.remove()


fig.legend(
    handles,
    labels,

    title=
        "Predictor specification",

    loc=
        "lower center",

    bbox_to_anchor=
        (0.5, -0.06),

    ncol=
        4,

    frameon=
        False
)


fig.suptitle(
    "Prediction Performance Across Predictor Specifications",
    y=1.02
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure5_predictor_set_performance"
)


plt.show()



# ============================================================
# SOURCE CELL In [86]:
# ============================================================
overall_comparison = (
    comparison_summary.loc[
        comparison_summary["Horizon"]
        == "Overall"
    ]
    .sort_values("MAE_mean")
    .reset_index(drop=True)
)

display(
    overall_comparison.round(3)
)



# ============================================================
# SOURCE CELL In [87]:
# ============================================================
best_parameters = pd.DataFrame(
    best_parameter_records
)

best_parameters["Parameter setting"] = (
    best_parameters["Best parameters"]
    .apply(
        lambda parameters: ", ".join(
            [
                f"{key}={value}"
                for key, value in sorted(
                    parameters.items()
                )
            ]
        )
    )
)

parameter_frequencies = (
    best_parameters
    .groupby(
        [
            "Model",
            "Parameter setting"
        ]
    )
    .size()
    .rename("Number of outer folds")
    .reset_index()
    .sort_values(
        [
            "Model",
            "Number of outer folds"
        ],
        ascending=[True, False]
    )
)

display(
    parameter_frequencies
)



# ============================================================
# SOURCE CELL In [88]:
# ============================================================
OUTPUT_FOLDER = (
    DATA_DIR
    / "rtms_ml_results"
)

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

comparison_summary.to_csv(
    OUTPUT_FOLDER
    / "supervised_model_summary.csv",
    index=False
)

supervised_metrics.to_csv(
    OUTPUT_FOLDER
    / "supervised_repeated_metrics.csv",
    index=False
)

best_parameters.assign(
    **{
        "Best parameters":
            best_parameters[
                "Best parameters"
            ].astype(str)
    }
).to_csv(
    OUTPUT_FOLDER
    / "selected_hyperparameters.csv",
    index=False
)

prediction_arrays = {
    "observed_outcomes": Y_array,
    "participants":
        model_complete.index.to_numpy(dtype=str)
}

for model_name, predictions in (
    all_model_predictions.items()
):
    safe_name = (
        model_name
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    prediction_arrays[
        safe_name
    ] = predictions

np.savez_compressed(
    OUTPUT_FOLDER
    / "out_of_fold_predictions.npz",
    **prediction_arrays
)

print("Part 5 results saved to:")
print(OUTPUT_FOLDER)



# ============================================================
# SOURCE CELL In [89]:
# ============================================================
#Part 6 — Mixed-effects model comparison
import statsmodels.formula.api as smf
import warnings
import time

print("Statsmodels imported successfully.")



# ============================================================
# SOURCE CELL In [90]:
# ============================================================
mixed_participant_data = model_complete.copy()

mixed_participant_data["Participant"] = (
    mixed_participant_data.index.astype(str)
)

CLINICAL_DOMAIN_GROUPS = {
    "memory": [
        "recall",
        "orientation",
        "word_recognition",
        "rti"
    ],
    "language_composite": [
        "naming",
        "commands",
        "language",
        "comprehension",
        "word_finding"
    ],
    "praxis": [
        "constructional_praxis",
        "ideational_praxis"
    ]
}

for visit_prefix in ["d3", "d5"]:
    for composite_name, domains in (
        CLINICAL_DOMAIN_GROUPS.items()
    ):
        source_columns = [
            f"{visit_prefix}_{domain}"
            for domain in domains
        ]

        mixed_participant_data[
            f"{visit_prefix}_{composite_name}"
        ] = (
            mixed_participant_data[
                source_columns
            ]
            .sum(axis=1)
        )

MIXED_NUMERIC_FEATURES = [
    "age",
    "b_total",
    "d3_memory",
    "d5_memory",
    "d3_language_composite",
    "d5_language_composite",
    "d3_praxis",
    "d5_praxis"
]

display(
    mixed_participant_data[
        MIXED_NUMERIC_FEATURES
    ].describe().T.round(3)
)



# ============================================================
# SOURCE CELL In [91]:
# ============================================================
MIXED_Z_FEATURES = [
    f"z_{feature}"
    for feature in MIXED_NUMERIC_FEATURES
]

MIXED_FORMULA = """
future_change
~ C(horizon) * C(treatment)
+ z_age
+ z_b_total
+ z_d3_memory
+ z_d5_memory
+ z_d3_language_composite
+ z_d5_language_composite
+ z_d3_praxis
+ z_d5_praxis
+ C(sex)
+ C(site)
"""

MIXED_FORMULA = " ".join(
    MIXED_FORMULA.split()
)

print(MIXED_FORMULA)



# ============================================================
# SOURCE CELL In [92]:
# ============================================================
# Corrected Part 6 datatype compatibility cell

def create_mixed_long_data(participant_data):

    identifier_columns = [
        "Participant",
        "treatment",
        "sex",
        "site"
    ] + MIXED_Z_FEATURES

    long_data = (
        participant_data[
            identifier_columns + OUTCOME_COLUMNS
        ]
        .melt(
            id_vars=identifier_columns,
            value_vars=OUTCOME_COLUMNS,
            var_name="horizon",
            value_name="future_change"
        )
    )

    long_data["horizon"] = long_data["horizon"].map({
        "y_8": "8",
        "y_16": "16",
        "y_24": "24"
    })

    # Compatibility fix for older statsmodels/patsy
    categorical_columns = [
        "Participant",
        "treatment",
        "sex",
        "site",
        "horizon"
    ]

    for column in categorical_columns:
        long_data[column] = (
            long_data[column]
            .astype(str)
            .astype(object)
        )

    # Explicitly ensure all model quantities are numeric
    long_data["future_change"] = pd.to_numeric(
        long_data["future_change"],
        errors="raise"
    )

    for column in MIXED_Z_FEATURES:
        long_data[column] = pd.to_numeric(
            long_data[column],
            errors="raise"
        )

    # Set the intended reference/order for the horizons
    long_data["horizon"] = pd.Categorical(
        long_data["horizon"],
        categories=["8", "16", "24"],
        ordered=True
    )

    return long_data



# ============================================================
# SOURCE CELL In [93]:
# ============================================================
def fit_mixed_model(
    training_long_data
):
    fitting_methods = [
        "lbfgs",
        "powell",
        "cg"
    ]

    last_error = None
    best_result = None
    best_method = None

    for method in fitting_methods:
        try:
            model = smf.mixedlm(
                formula=MIXED_FORMULA,
                data=training_long_data,
                groups=training_long_data[
                    "Participant"
                ],
                re_formula="1"
            )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                result = model.fit(
                    reml=False,
                    method=method,
                    maxiter=2000,
                    disp=False
                )

            finite_coefficients = np.all(
                np.isfinite(
                    result.fe_params.to_numpy()
                )
            )

            if finite_coefficients:
                best_result = result
                best_method = method

                if result.converged:
                    break

        except Exception as error:
            last_error = error

    if best_result is None:
        raise RuntimeError(
            "Mixed model failed with all fitting methods. "
            f"Last error: {last_error}"
        )

    return best_result, best_method



# ============================================================
# SOURCE CELL In [94]:
# ============================================================
mixed_predictions = np.full(
    (
        N_REPEATS,
        len(model_complete),
        len(OUTCOME_COLUMNS)
    ),
    np.nan
)

mixed_fit_records = []

print(
    "Mixed prediction array:",
    mixed_predictions.shape
)



# ============================================================
# SOURCE CELL In [95]:
# ============================================================
mixed_start_time = time.time()

for split_number, (train_indices, test_indices) in enumerate(
    outer_splits
):
    repeat_index = split_number // N_SPLITS
    fold_index = split_number % N_SPLITS

    training_participants = (
        mixed_participant_data
        .iloc[train_indices]
        .copy()
    )

    testing_participants = (
        mixed_participant_data
        .iloc[test_indices]
        .copy()
    )

    # Standardize using training participants only
    training_means = training_participants[
        MIXED_NUMERIC_FEATURES
    ].mean()

    training_standard_deviations = (
        training_participants[
            MIXED_NUMERIC_FEATURES
        ]
        .std(ddof=0)
        .replace(0, 1)
    )

    for feature in MIXED_NUMERIC_FEATURES:
        training_participants[
            f"z_{feature}"
        ] = (
            training_participants[feature]
            - training_means[feature]
        ) / training_standard_deviations[feature]

        testing_participants[
            f"z_{feature}"
        ] = (
            testing_participants[feature]
            - training_means[feature]
        ) / training_standard_deviations[feature]

    training_long = create_mixed_long_data(
        training_participants
    )

    testing_long = create_mixed_long_data(
        testing_participants
    )

    result, selected_method = fit_mixed_model(
        training_long
    )

    # For unseen test participants, prediction uses fixed
    # effects only. Test random effects are not estimated.
    test_predictions_long = result.predict(
        testing_long
    )

    prediction_frame = testing_long[
        ["Participant", "horizon"]
    ].copy()

    prediction_frame["prediction"] = (
        np.asarray(test_predictions_long)
    )

    prediction_wide = prediction_frame.pivot(
        index="Participant",
        columns="horizon",
        values="prediction"
    )

    test_participant_order = (
        mixed_participant_data
        .iloc[test_indices][
            "Participant"
        ]
        .tolist()
    )

    prediction_wide = prediction_wide.reindex(
        index=test_participant_order,
        columns=["8", "16", "24"]
    )

    mixed_predictions[
        repeat_index,
        test_indices,
        :
    ] = prediction_wide.to_numpy()

    random_intercept_variance = np.nan

    try:
        random_intercept_variance = float(
            result.cov_re.iloc[0, 0]
        )
    except Exception:
        pass

    mixed_fit_records.append({
        "Repeat": repeat_index + 1,
        "Fold": fold_index + 1,
        "Outer split": split_number + 1,
        "Training participants":
            len(train_indices),
        "Test participants":
            len(test_indices),
        "Method": selected_method,
        "Converged":
            bool(result.converged),
        "Random-intercept variance":
            random_intercept_variance
    })

    print(
        f"Split {split_number + 1:02d}/"
        f"{len(outer_splits)}: "
        f"method={selected_method}, "
        f"converged={result.converged}"
    )

print("\nMixed-effects cross-validation completed.")
print(
    "Elapsed minutes:",
    round(
        (time.time() - mixed_start_time)
        / 60,
        2
    )
)



# ============================================================
# SOURCE CELL In [96]:
# ============================================================
mixed_fit_log = pd.DataFrame(
    mixed_fit_records
)

display(mixed_fit_log)

print("\nConvergence summary:")

display(
    mixed_fit_log[
        ["Method", "Converged"]
    ]
    .value_counts()
    .rename("Outer folds")
    .to_frame()
)

print(
    "\nMissing predictions:",
    np.isnan(mixed_predictions).sum()
)

assert not np.isnan(
    mixed_predictions
).any()



# ============================================================
# SOURCE CELL In [97]:
# ============================================================
mixed_metrics = calculate_repeated_metrics(
    observed=Y_array,
    repeated_predictions=mixed_predictions,
    model_name="Mixed-effects model",
    outcome_names=OUTCOME_COLUMNS
)

mixed_summary = (
    mixed_metrics
    .groupby(["Model", "Horizon"])
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
)

display(
    mixed_summary.round(3)
)



# ============================================================
# SOURCE CELL In [98]:
# ============================================================
all_metrics_with_mixed = pd.concat(
    [
        comparison_metrics,
        mixed_metrics
    ],
    ignore_index=True
)

FINAL_MODEL_ORDER = [
    "Ridge regression",
    "Multi-task elastic net",
    "Restricted random forest",
    "Mixed-effects model"
]

final_summary = (
    all_metrics_with_mixed
    .groupby(["Model", "Horizon"])
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_sd=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_sd=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_sd=("R2", "std")
    )
    .reset_index()
)

final_summary["Model"] = pd.Categorical(
    final_summary["Model"],
    categories=FINAL_MODEL_ORDER,
    ordered=True
)

final_summary["Horizon"] = pd.Categorical(
    final_summary["Horizon"],
    categories=[
        "y_8",
        "y_16",
        "y_24",
        "Overall"
    ],
    ordered=True
)

final_summary = (
    final_summary
    .sort_values(["Horizon", "Model"])
    .reset_index(drop=True)
)

display(
    final_summary.round(3)
)



# ============================================================
# SOURCE CELL In [99]:
# ============================================================
final_overall_comparison = (
    final_summary.loc[
        final_summary["Horizon"]
        == "Overall"
    ]
    .sort_values("MAE_mean")
    .reset_index(drop=True)
)

display(
    final_overall_comparison.round(3)
)



# ============================================================
# SOURCE CELL In [100]:
# ============================================================
# ============================================================
# FIGURE 6
# MODEL-CLASS COMPARISON
# ============================================================

model_class_plot_data = (
    all_metrics_with_mixed.copy()
)


model_class_plot_data[
    "Horizon label"
] = (
    model_class_plot_data[
        "Horizon"
    ]
    .map(
        HORIZON_LABELS
    )
)


MODEL_CLASS_LABELS = {
    "Ridge regression":
        "Full-domain ridge",

    "Multi-task elastic net":
        "Multi-task elastic net",

    "Restricted random forest":
        "Random forest",

    "Mixed-effects model":
        "Mixed-effects model"
}


model_class_plot_data[
    "Model label"
] = (
    model_class_plot_data[
        "Model"
    ]
    .map(
        MODEL_CLASS_LABELS
    )
)


model_class_plot_data[
    "Horizon label"
] = pd.Categorical(
    model_class_plot_data[
        "Horizon label"
    ],

    categories=
        HORIZON_ORDER,

    ordered=
        True
)


model_class_order = [
    "Full-domain ridge",
    "Multi-task elastic net",
    "Random forest",
    "Mixed-effects model"
]


fig, axes = plt.subplots(
    1,
    2,
    figsize=(15, 5.5)
)


# ------------------------------------------------------------
# A. MAE
# ------------------------------------------------------------

sns.barplot(
    data=
        model_class_plot_data,

    x=
        "Horizon label",

    y=
        "MAE",

    hue=
        "Model label",

    hue_order=
        model_class_order,

    errorbar=
        "sd",

    capsize=
        0.10,

    ax=
        axes[0]
)


axes[0].set_title(
    "A. Mean Absolute Error"
)

axes[0].set_xlabel(
    "Prediction horizon"
)

axes[0].set_ylabel(
    "Mean absolute error"
)

axes[0].grid(
    axis="y",
    alpha=0.20
)


# ------------------------------------------------------------
# B. R-SQUARED
# ------------------------------------------------------------

sns.barplot(
    data=
        model_class_plot_data,

    x=
        "Horizon label",

    y=
        "R2",

    hue=
        "Model label",

    hue_order=
        model_class_order,

    errorbar=
        "sd",

    capsize=
        0.10,

    ax=
        axes[1]
)


axes[1].axhline(
    0,
    linestyle="--",
    linewidth=1,
    color="black"
)

axes[1].set_title(
    "B. Out-of-Sample $R^2$"
)

axes[1].set_xlabel(
    "Prediction horizon"
)

axes[1].set_ylabel(
    "Out-of-sample $R^2$"
)

axes[1].grid(
    axis="y",
    alpha=0.20
)


# ------------------------------------------------------------
# COMMON LEGEND
# ------------------------------------------------------------

if axes[1].legend_ is not None:
    axes[1].legend_.remove()


handles, labels = (
    axes[0]
    .get_legend_handles_labels()
)


if axes[0].legend_ is not None:
    axes[0].legend_.remove()


fig.legend(
    handles,
    labels,

    title=
        "Model",

    loc=
        "lower center",

    bbox_to_anchor=
        (0.5, -0.06),

    ncol=
        4,

    frameon=
        False
)


fig.suptitle(
    "Prediction Performance Across Model Classes",
    y=1.02
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure6_model_class_performance"
)


plt.show()



# ============================================================
# SOURCE CELL In [102]:
# ============================================================
mixed_metrics.to_csv(
    OUTPUT_FOLDER
    / "mixed_effects_repeated_metrics.csv",
    index=False
)

mixed_fit_log.to_csv(
    OUTPUT_FOLDER
    / "mixed_effects_fit_log.csv",
    index=False
)

final_summary.to_csv(
    OUTPUT_FOLDER
    / "final_model_comparison.csv",
    index=False
)

np.save(
    OUTPUT_FOLDER
    / "mixed_effects_predictions.npy",
    mixed_predictions
)

print("Part 6 results saved to:")
print(OUTPUT_FOLDER)



# ============================================================
# SOURCE CELL In [103]:
# ============================================================
# ============================================================
# PART 7A — UNCERTAINTY AND INTERPRETABILITY SETUP
# ============================================================

from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.base import clone

required_part7_objects = [
    "Y_array",
    "Y_model",
    "X_model_input",
    "model_complete",
    "outer_splits",
    "all_model_predictions",
    "mixed_predictions",
    "best_parameters",
    "domain_preprocessor",
    "OUTCOME_COLUMNS",
    "OUTPUT_FOLDER"
]

missing_objects = [
    name for name in required_part7_objects
    if name not in globals()
]

if missing_objects:
    raise RuntimeError(
        "Run Parts 1–6 first. Missing objects: "
        + ", ".join(missing_objects)
    )

print("All Part 7 prerequisites are available.")
print("Participants:", len(model_complete))
print("Prediction horizons:", OUTCOME_COLUMNS)



# ============================================================
# SOURCE CELL In [104]:
# ============================================================
# Combine every model into one prediction dictionary

part7_predictions = dict(all_model_predictions)
part7_predictions["Mixed-effects model"] = mixed_predictions

PART7_MODELS = [
    "Ridge regression",
    "Multi-task elastic net",
    "Restricted random forest",
    "Mixed-effects model"
]

prediction_checks = []

for model_name in PART7_MODELS:
    predictions = part7_predictions[model_name]

    prediction_checks.append({
        "Model": model_name,
        "Shape": str(predictions.shape),
        "Missing values": int(np.isnan(predictions).sum()),
        "Repeated-CV overall MAE": np.mean(
            np.abs(predictions - Y_array[None, :, :])
        )
    })

prediction_checks = pd.DataFrame(prediction_checks)

display(
    prediction_checks
    .sort_values("Repeated-CV overall MAE")
    .round(3)
)

assert prediction_checks["Missing values"].max() == 0



# ============================================================
# SOURCE CELL In [105]:
# ============================================================
# ============================================================
# PAIRED PARTICIPANT-LEVEL BOOTSTRAP
# ============================================================

RIDGE_MODEL = "Ridge regression"

COMPARATORS = [
    "Multi-task elastic net",
    "Restricted random forest",
    "Mixed-effects model"
]

BOOTSTRAP_REPLICATIONS = 10000
BOOTSTRAP_SEED = 20260827

bootstrap_rng = np.random.default_rng(BOOTSTRAP_SEED)

n_participants = len(model_complete)

# The same resampled participants are used for all comparisons
bootstrap_indices = bootstrap_rng.integers(
    low=0,
    high=n_participants,
    size=(BOOTSTRAP_REPLICATIONS, n_participants)
)

ridge_predictions = part7_predictions[RIDGE_MODEL]

def participant_level_mae(predictions, horizon_index=None):
    """
    Return one average absolute-error value per participant.

    The averaging is across CV repetitions and, for Overall,
    across all three horizons.
    """

    absolute_errors = np.abs(
        predictions - Y_array[None, :, :]
    )

    if horizon_index is None:
        # Average across repetitions and horizons
        return absolute_errors.mean(axis=(0, 2))

    # Average across repetitions for one horizon
    return absolute_errors[:, :, horizon_index].mean(axis=0)


horizon_definitions = [
    ("y_8", 0),
    ("y_16", 1),
    ("y_24", 2),
    ("Overall", None)
]

bootstrap_records = []

for comparator_name in COMPARATORS:

    comparison_prediction_array = part7_predictions[comparator_name]

    for horizon_name, horizon_index in horizon_definitions:

        ridge_loss = participant_level_mae(
            ridge_predictions,
            horizon_index
        )

        comparator_loss = participant_level_mae(
            comparison_prediction_array,
            horizon_index
        )

        # Negative values favor ridge
        participant_differences = (
            ridge_loss - comparator_loss
        )

        observed_difference = participant_differences.mean()

        bootstrap_differences = (
            participant_differences[bootstrap_indices]
            .mean(axis=1)
        )

        lower_ci, upper_ci = np.quantile(
            bootstrap_differences,
            [0.025, 0.975]
        )

        probability_ridge_lower = np.mean(
            bootstrap_differences < 0
        )

        if upper_ci < 0:
            interpretation = "Ridge lower MAE"
        elif lower_ci > 0:
            interpretation = "Comparator lower MAE"
        else:
            interpretation = "Difference uncertain"

        bootstrap_records.append({
            "Comparator": comparator_name,
            "Horizon": horizon_name,
            "Ridge MAE": ridge_loss.mean(),
            "Comparator MAE": comparator_loss.mean(),
            "MAE difference": observed_difference,
            "CI lower": lower_ci,
            "CI upper": upper_ci,
            "Bootstrap probability ridge lower": (
                probability_ridge_lower
            ),
            "Interpretation": interpretation
        })

bootstrap_results = pd.DataFrame(bootstrap_records)

display(
    bootstrap_results
    .sort_values(["Horizon", "MAE difference"])
    .round(4)
)



# ============================================================
# SOURCE CELL In [106]:
# ============================================================
# ============================================================
# WITHIN-TOLERANCE PREDICTION ACCURACY
# ============================================================

ACCURACY_TOLERANCES = [1.0, 2.0, 3.0]

accuracy_records = []

horizon_definitions = [
    ("Week 8", 0),
    ("Week 16", 1),
    ("Week 24", 2),
    ("Overall", None)
]

for model_name in PART7_MODELS:

    # Shape: repetitions × participants × horizons
    predictions = part7_predictions[model_name]

    for repeat_index in range(predictions.shape[0]):

        repeat_predictions = predictions[repeat_index]

        for horizon_name, horizon_index in horizon_definitions:

            if horizon_index is None:
                # All participants and all three horizons
                absolute_errors = np.abs(
                    repeat_predictions - Y_array
                )
            else:
                absolute_errors = np.abs(
                    repeat_predictions[:, horizon_index]
                    - Y_array[:, horizon_index]
                )

            for tolerance in ACCURACY_TOLERANCES:

                within_tolerance = (
                    absolute_errors <= tolerance
                )

                accuracy_records.append({
                    "Model": model_name,
                    "Repeat": repeat_index + 1,
                    "Horizon": horizon_name,
                    "Tolerance": tolerance,
                    "N predictions": absolute_errors.size,
                    "Within tolerance N":
                        int(within_tolerance.sum()),
                    "Within tolerance (%)":
                        100 * within_tolerance.mean()
                })

accuracy_by_repeat = pd.DataFrame(accuracy_records)

accuracy_summary = (
    accuracy_by_repeat
    .groupby(["Model", "Horizon", "Tolerance"])
    .agg(
        Accuracy_mean=(
            "Within tolerance (%)", "mean"
        ),
        Accuracy_SD=(
            "Within tolerance (%)", "std"
        ),
        Minimum_accuracy=(
            "Within tolerance (%)", "min"
        ),
        Maximum_accuracy=(
            "Within tolerance (%)", "max"
        )
    )
    .reset_index()
)

# Main ±3-point overall results
overall_accuracy_3 = (
    accuracy_summary.loc[
        (accuracy_summary["Tolerance"] == 3)
        & (accuracy_summary["Horizon"] == "Overall")
    ]
    .sort_values("Accuracy_mean", ascending=False)
)

display(overall_accuracy_3.round(2))

# Full results
display(
    accuracy_summary
    .sort_values(["Tolerance", "Horizon", "Accuracy_mean"],
                 ascending=[True, True, False])
    .round(2)
)

accuracy_by_repeat.to_csv(
    OUTPUT_FOLDER / "accuracy_by_repeat.csv",
    index=False
)

accuracy_summary.to_csv(
    OUTPUT_FOLDER / "within_tolerance_accuracy_summary.csv",
    index=False
)



# ============================================================
# SOURCE CELL In [107]:
# ============================================================
# ============================================================
# FIGURE 7
# PAIRED PARTICIPANT-BOOTSTRAP COMPARISON
#
# Reference model:
# Early total-response ridge
#
# Comparators:
# Early domain-response ridge
# Mixed-effects model
# ============================================================

PRIMARY_MODEL_NAME = (
    "C: Early total response"
)


primary_predictions = (
    comparator_predictions[
        PRIMARY_MODEL_NAME
    ]
)


primary_bootstrap_comparators = {

    "Early domain response":
        comparator_predictions[
            "D: Domain-specific response"
        ],

    "Mixed-effects model":
        mixed_predictions
}


observed_matrix = (
    model_complete[
        OUTCOME_COLUMNS
    ]
    .to_numpy(
        dtype=float
    )
)


assert (
    primary_predictions.shape
    ==
    mixed_predictions.shape
)

assert (
    primary_predictions.shape[1]
    ==
    len(
        model_complete
    )
)


BOOTSTRAP_REPLICATIONS = 10000
BOOTSTRAP_SEED = 20260827


bootstrap_rng = (
    np.random.default_rng(
        BOOTSTRAP_SEED
    )
)


n_participants = (
    len(
        model_complete
    )
)


bootstrap_indices = (
    bootstrap_rng.integers(
        low=0,

        high=
            n_participants,

        size=(
            BOOTSTRAP_REPLICATIONS,
            n_participants
        )
    )
)


def participant_mae(
    predictions,
    horizon_index=None
):

    absolute_errors = np.abs(
        predictions
        -
        observed_matrix[
            None,
            :,
            :
        ]
    )

    if horizon_index is None:

        return (
            absolute_errors
            .mean(
                axis=(0, 2)
            )
        )

    return (
        absolute_errors[
            :,
            :,
            horizon_index
        ]
        .mean(
            axis=0
        )
    )


bootstrap_horizons = [
    (
        "8 weeks",
        0
    ),

    (
        "16 weeks",
        1
    ),

    (
        "24 weeks",
        2
    ),

    (
        "Overall",
        None
    )
]


primary_bootstrap_records = []


for (
    comparator_name,
    comparator_prediction_array
) in primary_bootstrap_comparators.items():

    for (
        horizon_name,
        horizon_index
    ) in bootstrap_horizons:

        primary_loss = (
            participant_mae(
                primary_predictions,
                horizon_index
            )
        )

        comparator_loss = (
            participant_mae(
                comparator_prediction_array,
                horizon_index
            )
        )

        # Negative values favor early total-response ridge
        participant_difference = (
            primary_loss
            -
            comparator_loss
        )

        observed_difference = (
            participant_difference.mean()
        )

        bootstrap_difference = (
            participant_difference[
                bootstrap_indices
            ]
            .mean(
                axis=1
            )
        )

        (
            lower_ci,
            upper_ci
        ) = np.quantile(
            bootstrap_difference,
            [
                0.025,
                0.975
            ]
        )


        primary_bootstrap_records.append({

            "Comparator":
                comparator_name,

            "Horizon":
                horizon_name,

            "Early total-response MAE":
                primary_loss.mean(),

            "Comparator MAE":
                comparator_loss.mean(),

            "MAE difference":
                observed_difference,

            "CI lower":
                lower_ci,

            "CI upper":
                upper_ci,

            "Probability early total response has lower MAE":
                np.mean(
                    bootstrap_difference
                    < 0
                )
        })


primary_bootstrap_results = (
    pd.DataFrame(
        primary_bootstrap_records
    )
)


display(
    primary_bootstrap_results
    .round(4)
)


# Save numerical results
primary_bootstrap_results.to_csv(
    MANUSCRIPT_FIGURE_DIR
    /
    "primary_bootstrap_comparisons.csv",

    index=False
)


bootstrap_plot_data = (
    primary_bootstrap_results
    .copy()
)


bootstrap_plot_data[
    "Horizon"
] = pd.Categorical(
    bootstrap_plot_data[
        "Horizon"
    ],

    categories=[
        "8 weeks",
        "16 weeks",
        "24 weeks",
        "Overall"
    ],

    ordered=True
)


bootstrap_plot_data = (
    bootstrap_plot_data
    .sort_values(
        [
            "Horizon",
            "Comparator"
        ]
    )
    .reset_index(
        drop=True
    )
)


fig, ax = plt.subplots(
    figsize=(9.5, 6.5)
)


y_positions = np.arange(
    len(
        bootstrap_plot_data
    )
)


markers = {
    "Early domain response":
        "o",

    "Mixed-effects model":
        "s"
}


for row_index, row in (
    bootstrap_plot_data
    .iterrows()
):

    estimate = (
        row[
            "MAE difference"
        ]
    )

    lower_error = (
        estimate
        -
        row[
            "CI lower"
        ]
    )

    upper_error = (
        row[
            "CI upper"
        ]
        -
        estimate
    )


    ax.errorbar(
        estimate,

        y_positions[
            row_index
        ],

        xerr=np.array([
            [
                lower_error
            ],
            [
                upper_error
            ]
        ]),

        fmt=
            markers[
                row[
                    "Comparator"
                ]
            ],

        capsize=
            4,

        markersize=
            7
    )


ax.axvline(
    0,
    linestyle="--",
    linewidth=1,
    color="black"
)


bootstrap_y_labels = [
    (
        f"{row['Horizon']} — "
        f"{row['Comparator']}"
    )

    for _, row
    in bootstrap_plot_data.iterrows()
]


ax.set_yticks(
    y_positions
)

ax.set_yticklabels(
    bootstrap_y_labels
)


ax.set_xlabel(
    "MAE difference: early total response − comparator\n"
    "(negative values favor early total response)"
)

ax.set_ylabel("")


ax.set_title(
    "Paired Participant-Bootstrap Differences in Prediction Error"
)


ax.grid(
    axis="x",
    alpha=0.25
)

ax.grid(
    axis="y",
    visible=False
)


legend_handles = [

    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="none",
        label="Early domain response"
    ),

    Line2D(
        [0],
        [0],
        marker="s",
        linestyle="none",
        label="Mixed-effects model"
    )
]


ax.legend(
    handles=
        legend_handles,

    title=
        "Comparator",

    frameon=
        False
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure7_bootstrap_mae_differences"
)


plt.show()



# ============================================================
# SOURCE CELL In [108]:
# ============================================================
# ============================================================
# FIGURE 8
# OBSERVED VERSUS PREDICTED ADAS-COG CHANGE
# EARLY TOTAL-RESPONSE RIDGE
# ============================================================

primary_predictions = (
    comparator_predictions[
        "C: Early total response"
    ]
)


observed_matrix = (
    model_complete[
        OUTCOME_COLUMNS
    ]
    .to_numpy(
        dtype=float
    )
)


mean_primary_predictions = (
    primary_predictions
    .mean(
        axis=0
    )
)


calibration_records = []


fig, axes = plt.subplots(
    1,
    3,
    figsize=(15.5, 5),
    constrained_layout=True
)


for (
    outcome_index,
    outcome_name
) in enumerate(
    OUTCOME_COLUMNS
):

    observed = (
        observed_matrix[
            :,
            outcome_index
        ]
    )

    predicted = (
        mean_primary_predictions[
            :,
            outcome_index
        ]
    )


    calibration_X = (
        sm.add_constant(
            predicted
        )
    )


    calibration_model = (
        sm.OLS(
            observed,
            calibration_X
        )
        .fit()
    )


    intercept = (
        calibration_model
        .params[0]
    )

    slope = (
        calibration_model
        .params[1]
    )


    confidence_intervals = (
        calibration_model
        .conf_int(
            alpha=0.05
        )
    )


    calibration_records.append({

        "Horizon":
            HORIZON_LABELS[
                outcome_name
            ],

        "Calibration intercept":
            intercept,

        "Intercept CI lower":
            confidence_intervals[
                0,
                0
            ],

        "Intercept CI upper":
            confidence_intervals[
                0,
                1
            ],

        "Calibration slope":
            slope,

        "Slope CI lower":
            confidence_intervals[
                1,
                0
            ],

        "Slope CI upper":
            confidence_intervals[
                1,
                1
            ]
    })


    minimum_value = min(
        observed.min(),
        predicted.min()
    )

    maximum_value = max(
        observed.max(),
        predicted.max()
    )


    axes[
        outcome_index
    ].scatter(
        predicted,
        observed,
        alpha=0.70,
        s=42
    )


    # Ideal prediction line
    axes[
        outcome_index
    ].plot(
        [
            minimum_value,
            maximum_value
        ],
        [
            minimum_value,
            maximum_value
        ],

        linestyle=
            "--",

        linewidth=
            1,

        color=
            "black",

        label=
            "Ideal"
    )


    # Estimated calibration line
    calibration_x = np.linspace(
        minimum_value,
        maximum_value,
        100
    )


    calibration_y = (
        intercept
        +
        slope
        *
        calibration_x
    )


    axes[
        outcome_index
    ].plot(
        calibration_x,
        calibration_y,
        linewidth=1.5,
        label="Estimated calibration"
    )


    axes[
        outcome_index
    ].set_title(
        HORIZON_LABELS[
            outcome_name
        ]
    )


    axes[
        outcome_index
    ].set_xlabel(
        "Mean out-of-fold predicted change"
    )


    axes[
        outcome_index
    ].set_ylabel(
        "Observed ADAS-Cog change"
    )


    axes[
        outcome_index
    ].text(
        0.04,
        0.96,

        (
            f"Intercept = {intercept:.2f}\n"
            f"Slope = {slope:.2f}"
        ),

        transform=
            axes[
                outcome_index
            ].transAxes,

        va=
            "top",

        ha=
            "left"
    )


    axes[
        outcome_index
    ].grid(
        alpha=0.20
    )


handles, labels = (
    axes[0]
    .get_legend_handles_labels()
)


fig.legend(
    handles,
    labels,

    loc=
        "lower center",

    bbox_to_anchor=
        (0.5, -0.03),

    ncol=
        2,

    frameon=
        False
)


fig.suptitle(
    "Early Total-Response Ridge: Observed and Predicted ADAS-Cog Change",
    y=1.03
)


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figure8_observed_predicted_calibration"
)


plt.show()


# ------------------------------------------------------------
# CALIBRATION TABLE
# ------------------------------------------------------------

calibration_table = (
    pd.DataFrame(
        calibration_records
    )
    .round(3)
)


display(
    calibration_table
)


calibration_table.to_csv(
    MANUSCRIPT_FIGURE_DIR
    /
    "early_total_response_calibration.csv",

    index=False
)



# ============================================================
# SOURCE CELL In [111]:
# ============================================================
# ============================================================
# PART 7G — RIDGE COEFFICIENT STABILITY ACROSS OUTER FOLDS
# Compatible with older scikit-learn versions
# ============================================================

coefficient_records = []

# Retrieve the hyperparameter selected for ridge regression
# in each outer cross-validation split
ridge_parameter_rows = (
    best_parameters.loc[
        best_parameters["Model"] == "Ridge regression"
    ]
    .set_index("Outer split")
)

print(
    "Ridge regression parameter records:",
    len(ridge_parameter_rows)
)

assert len(ridge_parameter_rows) == len(outer_splits), (
    "The number of ridge parameter records does not match "
    "the number of outer CV splits."
)


for split_number, (train_indices, test_indices) in enumerate(
    outer_splits,
    start=1
):

    # --------------------------------------------------------
    # Obtain the alpha selected during nested cross-validation
    # --------------------------------------------------------

    selected_parameters = ridge_parameter_rows.loc[
        split_number,
        "Best parameters"
    ]

    selected_alpha = selected_parameters["model__alpha"]

    # --------------------------------------------------------
    # Refit ridge using only this outer training fold
    # --------------------------------------------------------

    ridge_pipeline = Pipeline(
        steps=[
            (
                "preprocess",
                clone(domain_preprocessor)
            ),
            (
                "model",
                Ridge(alpha=selected_alpha)
            )
        ]
    )

    ridge_pipeline.fit(
        X_model_input.iloc[train_indices],
        Y_model.iloc[train_indices]
    )

    fitted_preprocessor = (
        ridge_pipeline.named_steps["preprocess"]
    )

    fitted_ridge = (
        ridge_pipeline.named_steps["model"]
    )

    # --------------------------------------------------------
    # Manually reconstruct transformed feature names
    # This avoids get_feature_names_out() errors from the
    # older SimpleImputer/scikit-learn version.
    # --------------------------------------------------------

    numeric_feature_names = np.array([
        f"numeric__{feature}"
        for feature in NUMERIC_FEATURES
    ])

    fitted_categorical_pipeline = (
        fitted_preprocessor
        .named_transformers_["categorical"]
    )

    fitted_encoder = (
        fitted_categorical_pipeline
        .named_steps["encoder"]
    )

    try:
        categorical_output_names = (
            fitted_encoder.get_feature_names_out(
                CATEGORICAL_FEATURES
            )
        )

    except AttributeError:
        categorical_output_names = (
            fitted_encoder.get_feature_names(
                CATEGORICAL_FEATURES
            )
        )

    categorical_feature_names = np.array([
        f"categorical__{feature}"
        for feature in categorical_output_names
    ])

    transformed_feature_names = np.concatenate([
        numeric_feature_names,
        categorical_feature_names
    ])

    # Ridge has one coefficient vector for each outcome
    coefficients = np.atleast_2d(
        fitted_ridge.coef_
    )

    # Verify that feature names and coefficients align
    assert (
        len(transformed_feature_names)
        == coefficients.shape[1]
    ), (
        "Feature-name count does not match coefficient count: "
        f"{len(transformed_feature_names)} names versus "
        f"{coefficients.shape[1]} coefficients "
        f"in outer split {split_number}."
    )

    # --------------------------------------------------------
    # Store coefficients for every outcome and feature
    # --------------------------------------------------------

    for outcome_index, outcome_name in enumerate(
        OUTCOME_COLUMNS
    ):

        for feature_name, coefficient in zip(
            transformed_feature_names,
            coefficients[outcome_index]
        ):

            if feature_name.startswith("numeric__"):

                readable_name = feature_name.replace(
                    "numeric__",
                    ""
                )

                feature_type = (
                    "Numeric: coefficient per 1 SD"
                )

            else:

                readable_name = feature_name.replace(
                    "categorical__",
                    ""
                )

                feature_type = "Categorical contrast"

            coefficient_records.append({
                "Outer split": split_number,
                "Repeat": (
                    (split_number - 1) // N_SPLITS + 1
                ),
                "Fold": (
                    (split_number - 1) % N_SPLITS + 1
                ),
                "Horizon": outcome_name,
                "Feature": readable_name,
                "Feature type": feature_type,
                "Alpha": selected_alpha,
                "Coefficient": float(coefficient)
            })


# ============================================================
# CREATE COEFFICIENT DATAFRAME
# ============================================================

ridge_coefficients = pd.DataFrame(
    coefficient_records
)

print(
    "Coefficient records created:",
    len(ridge_coefficients)
)

print(
    "Unique outer splits:",
    ridge_coefficients["Outer split"].nunique()
)

print(
    "Unique horizons:",
    ridge_coefficients["Horizon"].nunique()
)

print(
    "Unique transformed features:",
    ridge_coefficients["Feature"].nunique()
)

assert ridge_coefficients["Outer split"].nunique() == len(
    outer_splits
)

assert ridge_coefficients["Horizon"].nunique() == len(
    OUTCOME_COLUMNS
)


# ============================================================
# SUMMARIZE COEFFICIENT MAGNITUDE AND STABILITY
# ============================================================

coefficient_summary = (
    ridge_coefficients
    .groupby(
        [
            "Feature",
            "Feature type",
            "Horizon"
        ],
        as_index=False
    )
    .agg(
        Mean_coefficient=(
            "Coefficient",
            "mean"
        ),
        SD_coefficient=(
            "Coefficient",
            "std"
        ),
        Mean_absolute_coefficient=(
            "Coefficient",
            lambda values: np.mean(
                np.abs(values)
            )
        ),
        Minimum_coefficient=(
            "Coefficient",
            "min"
        ),
        Maximum_coefficient=(
            "Coefficient",
            "max"
        ),
        Positive_proportion=(
            "Coefficient",
            lambda values: np.mean(
                values > 0
            )
        )
    )
)

# Sign consistency ranges from 0.50 to 1.00.
# A value of 1.00 means the coefficient had the same sign
# in every outer fold.
coefficient_summary["Sign consistency"] = np.maximum(
    coefficient_summary["Positive_proportion"],
    1 - coefficient_summary["Positive_proportion"]
)

coefficient_summary["Stable direction"] = np.where(
    coefficient_summary["Sign consistency"] >= 0.80,
    "Yes",
    "No"
)

# Add readable horizon labels
coefficient_summary["Horizon label"] = (
    coefficient_summary["Horizon"].map({
        "y_8": "Week 8",
        "y_16": "Week 16",
        "y_24": "Week 24"
    })
)


# ============================================================
# DISPLAY THE LARGEST AND MOST STABLE COEFFICIENTS
# ============================================================

largest_coefficients = (
    coefficient_summary
    .sort_values(
        [
            "Mean_absolute_coefficient",
            "Sign consistency"
        ],
        ascending=[False, False]
    )
    .reset_index(drop=True)
)

display(
    largest_coefficients[
        [
            "Feature",
            "Feature type",
            "Horizon label",
            "Mean_coefficient",
            "SD_coefficient",
            "Mean_absolute_coefficient",
            "Sign consistency",
            "Stable direction"
        ]
    ]
    .head(30)
    .round(3)
)

print(
    "\nPart 7G completed successfully."
)



# ============================================================
# SOURCE CELL In [112]:
# ============================================================
# ============================================================
# SUPPLEMENTARY FIGURE S1
# FULL-DOMAIN RIDGE COEFFICIENT STABILITY
# ============================================================

numeric_coefficient_data = (
    ridge_coefficients.loc[
        ridge_coefficients[
            "Feature type"
        ]
        ==
        "Numeric: coefficient per 1 SD"
    ]
    .copy()
)


top_numeric_features = (
    numeric_coefficient_data
    .groupby(
        "Feature"
    )[
        "Coefficient"
    ]
    .apply(
        lambda values:
            np.mean(
                np.abs(
                    values
                )
            )
    )
    .sort_values(
        ascending=False
    )
    .head(12)
    .index
    .tolist()
)


numeric_coefficient_data[
    "Horizon label"
] = (
    numeric_coefficient_data[
        "Horizon"
    ]
    .map(
        HORIZON_LABELS
    )
)


def readable_predictor_name(
    feature
):

    if feature.startswith(
        "d3_"
    ):

        prefix = (
            "Week 3 change: "
        )

        name = (
            feature[
                3:
            ]
        )


    elif feature.startswith(
        "d5_"
    ):

        prefix = (
            "Week 5 change: "
        )

        name = (
            feature[
                3:
            ]
        )


    elif feature.startswith(
        "b_"
    ):

        prefix = (
            "Baseline: "
        )

        name = (
            feature[
                2:
            ]
        )


    else:

        prefix = ""
        name = feature


    name = (
        name
        .replace(
            "_",
            " "
        )
        .title()
    )


    name = (
        name
        .replace(
            "Rti",
            "Remembering Test Instructions"
        )
    )


    return (
        prefix
        +
        name
    )


coefficient_plot_data = (
    numeric_coefficient_data.loc[
        numeric_coefficient_data[
            "Feature"
        ]
        .isin(
            top_numeric_features
        )
    ]
    .copy()
)


coefficient_plot_data[
    "Predictor"
] = (
    coefficient_plot_data[
        "Feature"
    ]
    .map(
        readable_predictor_name
    )
)


feature_display_order = [
    readable_predictor_name(
        feature
    )

    for feature
    in top_numeric_features
]


fig, ax = plt.subplots(
    figsize=(11.5, 8)
)


sns.barplot(
    data=
        coefficient_plot_data,

    y=
        "Predictor",

    x=
        "Coefficient",

    hue=
        "Horizon label",

    order=
        feature_display_order,

    hue_order=[
        "8 weeks",
        "16 weeks",
        "24 weeks"
    ],

    errorbar=
        "sd",

    capsize=
        0.08,

    ax=
        ax
)


ax.axvline(
    0,
    linestyle="--",
    linewidth=1,
    color="black"
)


ax.set_title(
    "Standardized Ridge Coefficients Across Outer Cross-Validation Splits"
)


ax.set_xlabel(
    "Mean standardized coefficient with SD"
)

ax.set_ylabel("")


ax.legend(
    title=
        "Prediction horizon",

    bbox_to_anchor=
        (1.02, 1),

    loc=
        "upper left",

    frameon=
        False
)


ax.grid(
    axis="x",
    alpha=0.20
)

ax.grid(
    axis="y",
    visible=False
)


fig.tight_layout()


# SAVE IMMEDIATELY AFTER FIGURE GENERATION
save_manuscript_figure(
    fig,
    "figureS1_full_domain_ridge_coefficients"
)


plt.show()



# ============================================================
# SAVE KEY TABLES AND NUMERICAL RESULTS
# ============================================================

RESULTS_DIR = DATA_DIR / "rtms_clean_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

_tables_to_save = {
    "participant_flow.csv": globals().get("flow_summary"),
    "outcome_availability.csv": globals().get("outcome_availability"),
    "benchmark_summary.csv": globals().get("benchmark_summary"),
    "predictor_set_metrics.csv": globals().get("comparator_metrics"),
    "predictor_set_summary.csv": globals().get("comparator_summary"),
    "domain_incremental_value.csv": globals().get("incremental_summary"),
    "week3_sensitivity_summary.csv": globals().get("week3_sensitivity_summary"),
    "model_class_summary.csv": globals().get("final_summary"),
    "full_domain_bootstrap.csv": globals().get("bootstrap_results"),
    "primary_bootstrap_comparisons.csv": globals().get("primary_bootstrap_results"),
    "early_total_response_calibration.csv": globals().get("calibration_table"),
    "ridge_coefficient_summary.csv": globals().get("coefficient_summary"),
}

for filename, table in _tables_to_save.items():
    if isinstance(table, pd.DataFrame):
        table.to_csv(RESULTS_DIR / filename, index=False)
        print("Saved table:", RESULTS_DIR / filename)

print("\nAnalysis complete.")
print("Results folder:", RESULTS_DIR)
N_JOBS = int(os.environ.get("RTMS_N_JOBS", "-1"))
print("Figure folder:", MANUSCRIPT_FIGURE_DIR)
print("Parallel jobs:", N_JOBS)
