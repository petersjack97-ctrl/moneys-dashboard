import pandas as pd
import io
from parsers.merchant_cleaner import clean_merchant
from parsers.categorizer import normalize_category

# ── Chase (Sapphire, Freedom Flex, any Chase card) ───────────────────────────
# Columns: Transaction Date, Post Date, Description, Category, Type, Amount
# Amount sign: NEGATIVE = purchase (we negate to make expenses positive)
# Detect:  has "Transaction Date" + "Post Date" + "Type"

# ── American Express ──────────────────────────────────────────────────────────
# Columns: Date, Description, Amount, Extended Details, Appears On Your
#          Statement As, Address, City/State, Zip Code, Country, Reference,
#          Category
# Amount sign: POSITIVE = purchase (keep as-is)
# Detect: has "Extended Details" or "Appears On Your Statement As"

# ── Apple Card ────────────────────────────────────────────────────────────────
# Columns: Transaction Date, Clearing Date, Description, Merchant, Category,
#          Type, Amount (USD)
# Amount sign: NEGATIVE = purchase (we negate to make expenses positive)
# Detect: has "Merchant" + "Amount (USD)"


def detect_bank(columns: list[str]) -> str:
    cols = {c.lower() for c in columns}

    if "merchant" in cols and "amount (usd)" in cols:
        return "apple"

    if "extended details" in cols or "appears on your statement as" in cols:
        return "amex"

    if "transaction date" in cols and "post date" in cols and "type" in cols:
        return "chase"

    return "generic"


def _normalize_chase(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Transaction Date": "date",
        "Description": "description",
        "Category": "category",
        "Amount": "amount",
    })
    df = df[["date", "description", "amount", "category"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    # Chase: purchases are negative — negate so expenses are positive
    df["amount"] = df["amount"] * -1
    return df


def _normalize_amex(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Date": "date",
        "Description": "description",
        "Amount": "amount",
        "Category": "category",
    })
    keep = [c for c in ["date", "description", "amount", "category"] if c in df.columns]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    # Amex: purchases are already positive — keep as-is
    return df


def _normalize_apple(df: pd.DataFrame) -> pd.DataFrame:
    # Drop payment and debit rows (bill payments, direct debits)
    if "Type" in df.columns:
        df = df[~df["Type"].str.strip().str.lower().isin(["payment", "debit"])]

    # Use "Merchant" for cleaner names, fall back to "Description"
    description_col = "Merchant" if "Merchant" in df.columns else "Description"
    df = df.rename(columns={
        "Transaction Date": "date",
        description_col: "description",
        "Amount (USD)": "amount",
        "Category": "category",
    })
    keep = [c for c in ["date", "description", "amount", "category"] if c in df.columns]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    # Apple Card: purchases are positive, payments are negative — no negation needed
    return df


def _normalize_generic(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {c.lower(): c for c in df.columns}
    rename = {}
    for field in ["date", "description", "amount", "category"]:
        if field in col_map:
            rename[col_map[field]] = field
    df = df.rename(columns=rename)
    keep = [c for c in ["date", "description", "amount", "category"] if c in df.columns]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


_NORMALIZERS = {
    "chase": _normalize_chase,
    "amex": _normalize_amex,
    "apple": _normalize_apple,
    "generic": _normalize_generic,
}


def parse_uploaded_csv(uploaded_file, account_label: str = "") -> pd.DataFrame:
    content = uploaded_file.read()

    # Amex sometimes prepends blank/metadata lines — skip rows until we hit
    # a line that looks like a CSV header
    raw = content.decode("utf-8", errors="replace")
    lines = raw.splitlines()
    skip = 0
    for i, line in enumerate(lines):
        if "," in line and len(line.strip()) > 0:
            skip = i
            break
    df = pd.read_csv(io.BytesIO(content), skiprows=skip)

    bank = detect_bank(df.columns.tolist())
    normalizer = _NORMALIZERS.get(bank, _normalize_generic)
    df = normalizer(df)

    df = df.dropna(subset=["date", "amount"])

    if "category" not in df.columns:
        df["category"] = "Uncategorized"
    df["category"] = df["category"].fillna("Uncategorized")

    df["merchant_raw"] = df["description"].copy()
    df["description"] = df["description"].apply(clean_merchant)

    df["category"] = df.apply(
        lambda r: normalize_category(r["category"], r["description"]), axis=1
    )

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["account"] = account_label or uploaded_file.name

    return df
