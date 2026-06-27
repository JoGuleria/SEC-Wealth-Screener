import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SEC Public Equity Capacity Screener",
    layout="wide"
)

DATA_PATH = "data/processed/sec_capacity_scores.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


df = load_data()

st.title("SEC Public Equity Capacity Screener")

st.write(
    """
    This tool ranks SEC reporting owners using public-equity capacity signals from
    insider ownership filings. It is designed as a prospect research aid, not a
    net-worth estimator.
    """
)

# -----------------------------
# Sidebar filters
# -----------------------------

st.sidebar.header("Filters")

owner_types = sorted(df["owner_type"].dropna().unique())

selected_owner_types = st.sidebar.multiselect(
    "Owner Type",
    owner_types,
    default=["Individual"] if "Individual" in owner_types else owner_types
)

tiers = sorted(df["capacity_tier"].dropna().unique())

selected_tiers = st.sidebar.multiselect(
    "Capacity Tier",
    tiers,
    default=tiers
)

min_score = st.sidebar.slider(
    "Minimum Capacity Signal Score",
    min_value=0,
    max_value=100,
    value=50
)

search_name = st.sidebar.text_input("Search owner/person")
search_company = st.sidebar.text_input("Search company")
search_ticker = st.sidebar.text_input("Search ticker")

filtered = df.copy()

filtered = filtered[
    (filtered["owner_type"].isin(selected_owner_types)) &
    (filtered["capacity_tier"].isin(selected_tiers)) &
    (filtered["capacity_signal_score"] >= min_score)
]

if search_name:
    filtered = filtered[
        filtered["person_name"].str.contains(search_name, case=False, na=False)
    ]

if search_company:
    filtered = filtered[
        filtered["company_name"].str.contains(search_company, case=False, na=False)
    ]

if search_ticker:
    filtered = filtered[
        filtered["ticker"].str.contains(search_ticker, case=False, na=False)
    ]


# -----------------------------
# Metrics
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Records", f"{len(filtered):,}")
col2.metric("Unique Owners", f"{filtered['person_name'].nunique():,}")
col3.metric("Companies", f"{filtered['company_name'].nunique():,}")

if len(filtered) > 0:
    col4.metric("Top Score", f"{filtered['capacity_signal_score'].max():.1f}")
else:
    col4.metric("Top Score", "N/A")


# -----------------------------
# Tabs
# -----------------------------

tab1, tab2, tab3 = st.tabs(
    ["Ranked Signals", "Signal Profile", "Methodology"]
)


with tab1:
    st.subheader("Ranked Public Equity Capacity Signals")

    display_cols = [
        "person_name",
        "owner_type",
        "company_name",
        "ticker",
        "capacity_signal_score",
        "capacity_tier",
        "total_reported_transaction_value",
        "open_market_transaction_value",
        "max_transaction_value",
        "filing_count",
        "role_score",
        "why_surfaced"
    ]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    csv = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered CSV",
        data=csv,
        file_name="filtered_sec_capacity_scores.csv",
        mime="text/csv"
    )


with tab2:
    st.subheader("Owner / Prospect Signal Profile")

    if len(filtered) == 0:
        st.warning("No records match your current filters.")
    else:
        filtered = filtered.reset_index(drop=True)

        selected_label = st.selectbox(
            "Select a record",
            filtered["person_name"] + " — " + filtered["company_name"]
        )

        selected_row = filtered[
            (filtered["person_name"] + " — " + filtered["company_name"]) == selected_label
        ].iloc[0]

        left, right = st.columns([1, 2])

        with left:
            st.metric(
                "Capacity Signal Score",
                selected_row["capacity_signal_score"]
            )

            st.write(f"**Tier:** {selected_row['capacity_tier']}")
            st.write(f"**Owner Type:** {selected_row['owner_type']}")
            st.write(f"**Company:** {selected_row['company_name']}")
            st.write(f"**Ticker:** {selected_row['ticker']}")
            st.write(f"**Role Score:** {selected_row['role_score']}")

        with right:
            st.write("### Why this record surfaced")
            st.write(selected_row["why_surfaced"])

            st.write("### Public equity signal details")

            st.write(
                f"**Total reported transaction value:** "
                f"${selected_row['total_reported_transaction_value']:,.0f}"
            )

            st.write(
                f"**Open-market purchase/sale value:** "
                f"${selected_row['open_market_transaction_value']:,.0f}"
            )

            st.write(
                f"**Largest single transaction value:** "
                f"${selected_row['max_transaction_value']:,.0f}"
            )

            st.write(
                f"**Grant/award value:** "
                f"${selected_row['grant_award_value']:,.0f}"
            )

            st.write(
                f"**Option exercise value:** "
                f"${selected_row['option_exercise_value']:,.0f}"
            )

            st.write(
                f"**Gift value:** "
                f"${selected_row['gift_value']:,.0f}"
            )

            st.write(f"**Filing count:** {selected_row['filing_count']}")


with tab3:
    st.subheader("Methodology")

    st.write(
        """
        This tool uses public SEC Form 3, Form 4, and Form 5 insider ownership data
        to identify visible public-equity capacity signals.

        The capacity signal score is based on:

        - Total reported transaction value
        - Open-market purchase/sale value
        - Largest single transaction value
        - Filing activity
        - Reporting owner role strength
        - Owner type classification

        The tool separates individual reporting owners from entities such as trusts,
        funds, partnerships, LLCs, holding companies, and investment managers.

        The score does **not** estimate total net worth. It only identifies visible
        public-equity activity from SEC filings.
        """
    )

    st.warning(
        """
        This tool should be used only as a prospect research aid. It should not be used
        for credit, housing, employment, insurance, eligibility, or financial decision-making.
        """
    )