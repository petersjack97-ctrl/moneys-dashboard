import pandas as pd
import io

# Known column mappings for common bank CSV formats
# Each entry: (date_col, description_col, amount_col, optional_category_col)
BANK_FORMATS = {
    "chase": {
        "date": "Transaction Date",
        "description": "Description",
        "amount": "Amount",
        "category": "Category",
    },
    "bank_of_america": {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "category": None,
    },
    "td_bank": {
        "date": "Date",
        "description": "Description",
        "amount": "Debit",
        "category": None,
    },
    "generic": {
        "date": "date",
        "description": "description",
        "amount": "amount",
        "category": None,
    },
}


def detect_bank(columns: list[str]) -> str:
    cols_lower = [c.lower() for c in columns]
    if "transaction date" in cols_lower:
        return "chase"
    if "debit" in cols_lower and "credit" in cols_lower:
        return "td_bank"
    return "generic"


def normalize(df: pd.DataFrame, mapping: dict, bank: str) -> pd.DataFrame:
    renamed = {}

    renamed[mapping["date"]] = "date"
    renamed[mapping["description"]] = "description"

    # Handle debit/credit split (TD Bank style)
    if bank == "td_bank" and "Debit" in df.columns and "Credit" in df.columns:
        df["amount"] = df["Debit"].fillna(0) - df["Credit"].fillna(0)
        renamed[mapping["amount"]] = "amount" if mapping["amount"] in df.columns else None
    else:
        renamed[mapping["amount"]] = "amount"

    if mapping.get("category") and mapping["category"] in df.columns:
        renamed[mapping["category"]] = "category"

    df = df.rename(columns={k: v for k, v in renamed.items() if k in df.columns and v})

    # Keep only the columns we care about
    keep = [c for c in ["date", "description", "amount", "category"] if c in df.columns]
    df = df[keep]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])

    if "category" not in df.columns:
        df["category"] = "Uncategorized"

    df["month"] = df["date"].dt.to_period("M").astype(str)

    return df


def parse_uploaded_csv(uploaded_file, account_label: str = "") -> pd.DataFrame:
    content = uploaded_file.read()
    df = pd.read_csv(io.BytesIO(content))

    bank = detect_bank(df.columns.tolist())
    mapping = BANK_FORMATS.get(bank, BANK_FORMATS["generic"])

    # Remap generic format to actual column names if needed
    if bank == "generic":
        col_map = {c.lower(): c for c in df.columns}
        for key in ["date", "description", "amount"]:
            if key in col_map:
                mapping[key] = col_map[key]

    df = normalize(df, mapping, bank)
    df["account"] = account_label or uploaded_file.name
    return df
