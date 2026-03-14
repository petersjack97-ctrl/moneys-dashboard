import streamlit as st
import pandas as pd
import plotly.express as px
from parsers.csv_parser import parse_uploaded_csv
from db.database import load_transactions, insert_transactions, get_transaction_count

st.set_page_config(page_title="Moneys Dashboard", layout="wide")
st.title("Moneys")

# ── Sidebar: import new CSVs ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Import Transactions")
    uploaded_files = st.file_uploader(
        "Upload CSVs to add to database",
        type="csv",
        accept_multiple_files=True,
    )
    st.caption("Supports Chase (Sapphire, Freedom Flex), Amex, Apple Card, and generic CSVs.")

    if uploaded_files and st.button("Import", type="primary"):
        total_inserted = 0
        total_skipped = 0
        for f in uploaded_files:
            try:
                df = parse_uploaded_csv(f, account_label=f.name.replace(".csv", ""))
                expenses = df[df["amount"] > 0].copy()
                inserted, skipped = insert_transactions(expenses)
                total_inserted += inserted
                total_skipped += skipped
            except Exception as e:
                st.warning(f"Could not parse {f.name}: {e}")

        if total_inserted > 0:
            st.success(f"Added {total_inserted} new transactions.")
        if total_skipped > 0:
            st.info(f"Skipped {total_skipped} duplicates.")
        st.rerun()

    st.divider()
    st.caption(f"Database: {get_transaction_count():,} transactions")

# ── Load data from database ───────────────────────────────────────────────────
data = load_transactions()

if data.empty:
    st.info("No transactions yet. Upload CSVs from the sidebar to get started.")
    st.stop()

expenses_all = data[data["amount"] > 0].copy()

# ── Sidebar: month filter ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    months = sorted(expenses_all["month"].unique())
    selected_months = st.multiselect("Month", months, default=months)

# ── Page-level filters (category + card) ─────────────────────────────────────
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    categories = sorted(expenses_all["category"].unique())
    selected_categories = st.multiselect(
        "Filter by category",
        options=categories,
        default=categories,
    )

with filter_col2:
    cards = sorted(expenses_all["card"].unique())
    selected_cards = st.multiselect(
        "Filter by card",
        options=cards,
        default=cards,
    )

# ── Apply all filters ─────────────────────────────────────────────────────────
expenses = expenses_all[
    expenses_all["month"].isin(selected_months)
    & expenses_all["card"].isin(selected_cards)
    & expenses_all["category"].isin(selected_categories)
]

# ── KPI row ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Total Spent", f"${expenses['amount'].sum():,.2f}")
col2.metric("Transactions", f"{len(expenses):,}")
col3.metric("Avg per Transaction", f"${expenses['amount'].mean():,.2f}" if len(expenses) else "$0")

st.divider()

# ── Charts ───────────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Spending by Category")
    cat_totals = expenses.groupby("category")["amount"].sum().reset_index()
    fig_cat = px.pie(cat_totals, names="category", values="amount", hole=0.4)
    fig_cat.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_cat, use_container_width=True)

with right:
    st.subheader("Spending by Month")
    month_totals = expenses.groupby("month")["amount"].sum().reset_index()
    fig_month = px.bar(
        month_totals,
        x="month",
        y="amount",
        labels={"month": "Month", "amount": "Spent ($)"},
    )
    st.plotly_chart(fig_month, use_container_width=True)

st.subheader("Top 20 Merchants")
merchant_totals = (
    expenses.groupby("description")["amount"]
    .sum()
    .reset_index()
    .sort_values("amount", ascending=False)
    .head(20)
)
fig_merch = px.bar(
    merchant_totals,
    x="amount",
    y="description",
    orientation="h",
    labels={"amount": "Spent ($)", "description": "Merchant"},
)
fig_merch.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_merch, use_container_width=True)

# ── Raw transactions table ────────────────────────────────────────────────────
with st.expander("Raw Transactions"):
    display_cols = ["date", "description", "merchant_raw", "amount", "category", "card"]
    show_cols = [c for c in display_cols if c in expenses.columns]
    st.dataframe(
        expenses[show_cols].sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
