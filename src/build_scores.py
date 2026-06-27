import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


RAW_ZIP = Path("data/raw/2026q1_form345.zip")
OUTPUT = Path("data/processed/sec_capacity_scores.csv")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def read_tsv_from_zip(zip_file, filename):
    """Read a TSV file from the SEC ZIP and normalize column names."""
    with zip_file.open(filename) as f:
        df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


def to_number(series):
    """Convert a pandas Series to numeric safely."""
    return pd.to_numeric(series, errors="coerce")


def calculate_role_score(row):
    """
    Scores the reporting owner's relationship to the issuer.

    Uses text fields because the downloaded SEC file has:
    - rptowner_relationship
    - rptowner_title
    - rptowner_txt

    Not separate boolean columns.
    """
    relationship = str(row.get("rptowner_relationship", "")).lower()
    title = str(row.get("rptowner_title", "")).lower()
    txt = str(row.get("rptowner_txt", "")).lower()

    combined = " ".join([relationship, title, txt])

    score = 0

    officer_keywords = [
        "officer",
        "ceo",
        "chief executive",
        "cfo",
        "chief financial",
        "coo",
        "chief operating",
        "president",
        "chief legal",
        "general counsel",
        "chief accounting",
        "chairman",
        "chair",
        "executive",
        "principal financial",
        "principal accounting",
    ]

    if any(keyword in combined for keyword in officer_keywords):
        score += 30

    if "director" in combined:
        score += 25

    if (
        "10%" in combined
        or "ten percent" in combined
        or "tenpercent" in combined
        or "ten-percent" in combined
    ):
        score += 25

    if "other" in combined:
        score += 10

    return min(score, 40)


def classify_owner_type(name):
    """
    Separates individual prospects from entities such as trusts, funds, LPs, LLCs,
    holding companies, banks, and investment managers.
    """
    name = str(name).lower().strip()

    entity_keywords = [
        " llc", "l.l.c", " llc.",
        " lp", "l.p", " l.p.",
        " inc", "inc.", " incorporated",
        " corp", "corp.", " corporation",
        " company", " co.", " co ",
        " trust",
        " foundation",
        " fund",
        " funds",
        " partners",
        " partnership",
        " capital",
        " holdings",
        " holding",
        " management",
        " manager",
        " group",
        " insurance",
        " bank",
        " associates",
        " ventures",
        " limited",
        " ltd", "ltd.",
        " plc",
        " s.a.",
        " s.a ",
        " gmbh",
        " ag",
        " bv",
        " b.v.",
        " nv",
        " n.v.",
        " pte",
        " llp",
        " l.l.p",
    ]

    if any(keyword in f" {name} " for keyword in entity_keywords):
        return "Entity"

    return "Individual"


def classify_transaction_code(code):
    """
    Classifies SEC transaction codes into more readable categories.

    P = Open-market or private purchase
    S = Open-market or private sale
    A = Grant / award
    M = Option exercise or conversion
    G = Gift
    F = Tax withholding / payment
    D = Disposition to issuer
    """
    code = str(code).upper().strip()

    if code == "P":
        return "Open Market Purchase"
    elif code == "S":
        return "Open Market Sale"
    elif code == "A":
        return "Grant/Award"
    elif code == "M":
        return "Option Exercise"
    elif code == "G":
        return "Gift"
    elif code == "F":
        return "Tax/Withholding"
    elif code == "D":
        return "Disposition to Issuer"
    else:
        return "Other"


def assign_tier(score):
    if score >= 85:
        return "Tier 1: Very Strong Public Equity Signal"
    elif score >= 70:
        return "Tier 2: Strong Public Equity Signal"
    elif score >= 50:
        return "Tier 3: Moderate Public Equity Signal"
    else:
        return "Tier 4: Limited Public Equity Signal"


def explain(row):
    reasons = []

    if row["owner_type"] == "Entity":
        reasons.append("reported owner appears to be an entity rather than an individual")

    if row["total_reported_transaction_value"] >= 1_000_000:
        reasons.append("high total reported transaction value")
    elif row["total_reported_transaction_value"] >= 100_000:
        reasons.append("meaningful reported transaction value")

    if row["max_transaction_value"] >= 500_000:
        reasons.append("large single reported transaction")

    if row["open_market_transaction_value"] >= 100_000:
        reasons.append("meaningful open-market purchase/sale activity")

    if row["role_score"] >= 30:
        reasons.append("officer/director/major-owner relationship")

    if row["filing_count"] >= 3:
        reasons.append("multiple SEC filings")

    if not reasons:
        reasons.append("appears in SEC insider data with limited visible transaction signal")

    return "Surfaced because of " + ", ".join(reasons) + "."


# -----------------------------
# Load SEC files
# -----------------------------

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    submission = read_tsv_from_zip(z, "SUBMISSION.tsv")
    owners = read_tsv_from_zip(z, "REPORTINGOWNER.tsv")
    trans = read_tsv_from_zip(z, "NONDERIV_TRANS.tsv")


print("SUBMISSION columns:")
print(submission.columns.tolist())

print("\nREPORTINGOWNER columns:")
print(owners.columns.tolist())

print("\nNONDERIV_TRANS columns:")
print(trans.columns.tolist())


# -----------------------------
# Merge company + owner + transaction data
# -----------------------------

df = owners.merge(
    submission,
    on="accession_number",
    how="left"
)

df = df.merge(
    trans,
    on="accession_number",
    how="left"
)


# -----------------------------
# Clean and engineer fields
# -----------------------------

df["trans_shares_num"] = to_number(df["trans_shares"])
df["trans_price_num"] = to_number(df["trans_pricepershare"])

df["transaction_value"] = df["trans_shares_num"] * df["trans_price_num"]
df["transaction_value"] = df["transaction_value"].replace([np.inf, -np.inf], np.nan)
df["transaction_value"] = df["transaction_value"].fillna(0)

df["person_name"] = df["rptownername"].astype(str).str.title()
df["company_name"] = df["issuername"].astype(str).str.title()
df["ticker"] = df["issuertradingsymbol"].astype(str).str.upper()

df["owner_type"] = df["person_name"].apply(classify_owner_type)
df["role_score"] = df.apply(calculate_role_score, axis=1)
df["transaction_type"] = df["trans_code"].apply(classify_transaction_code)

# Transaction-value buckets
df["open_market_value"] = np.where(
    df["trans_code"].isin(["P", "S"]),
    df["transaction_value"],
    0
)

df["grant_award_value"] = np.where(
    df["trans_code"].eq("A"),
    df["transaction_value"],
    0
)

df["option_exercise_value"] = np.where(
    df["trans_code"].eq("M"),
    df["transaction_value"],
    0
)

df["gift_value"] = np.where(
    df["trans_code"].eq("G"),
    df["transaction_value"],
    0
)


# -----------------------------
# Aggregate to owner-company level
# -----------------------------

agg = (
    df
    .groupby(["person_name", "owner_type", "company_name", "ticker"], dropna=False)
    .agg(
        total_reported_transaction_value=("transaction_value", "sum"),
        max_transaction_value=("transaction_value", "max"),
        open_market_transaction_value=("open_market_value", "sum"),
        grant_award_value=("grant_award_value", "sum"),
        option_exercise_value=("option_exercise_value", "sum"),
        gift_value=("gift_value", "sum"),
        transaction_count=("trans_code", "count"),
        filing_count=("accession_number", "nunique"),
        role_score=("role_score", "max")
    )
    .reset_index()
)


# -----------------------------
# Score records
# -----------------------------

agg["total_reported_transaction_value"] = agg["total_reported_transaction_value"].fillna(0)
agg["max_transaction_value"] = agg["max_transaction_value"].fillna(0)
agg["open_market_transaction_value"] = agg["open_market_transaction_value"].fillna(0)

agg["reported_value_pct"] = (
    agg["total_reported_transaction_value"].rank(pct=True) * 100
)

agg["open_market_value_pct"] = (
    agg["open_market_transaction_value"].rank(pct=True) * 100
)

agg["max_transaction_pct"] = (
    agg["max_transaction_value"].rank(pct=True) * 100
)

agg["activity_pct"] = (
    agg["filing_count"].rank(pct=True) * 100
)

agg["role_pct"] = (
    agg["role_score"].rank(pct=True) * 100
)


# Entity adjustment:
# Entities are still useful signals, but should not dominate an individual prospect screener.
agg["owner_type_adjustment"] = np.where(agg["owner_type"] == "Entity", -5, 0)


agg["capacity_signal_score"] = (
    0.35 * agg["reported_value_pct"] +
    0.25 * agg["open_market_value_pct"] +
    0.15 * agg["max_transaction_pct"] +
    0.10 * agg["activity_pct"] +
    0.15 * agg["role_pct"] +
    agg["owner_type_adjustment"]
).clip(lower=0, upper=100).round(1)


agg["capacity_tier"] = agg["capacity_signal_score"].apply(assign_tier)
agg["why_surfaced"] = agg.apply(explain, axis=1)


# Sort highest score first
agg = agg.sort_values("capacity_signal_score", ascending=False)


# -----------------------------
# Save output
# -----------------------------

agg.to_csv(OUTPUT, index=False)

print(f"\nSaved scored file to {OUTPUT}")
print("\nTop 20 records:")
print(agg.head(20))

print("\nOwner type distribution:")
print(agg["owner_type"].value_counts())

print("\nCapacity tier distribution:")
print(agg["capacity_tier"].value_counts())