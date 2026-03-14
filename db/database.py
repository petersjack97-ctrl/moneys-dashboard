import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent.parent / "moneys.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                date         TEXT    NOT NULL,
                description  TEXT,
                merchant_raw TEXT,
                amount       REAL    NOT NULL,
                category     TEXT,
                card         TEXT,
                month        TEXT,
                imported_at  TEXT    DEFAULT (date('now')),
                UNIQUE (date, merchant_raw, amount, card)
            )
        """)


def insert_transactions(df: pd.DataFrame) -> tuple[int, int]:
    """
    Insert rows from df into the transactions table.
    Skips rows that violate the unique constraint (duplicates).
    Returns (inserted, skipped).
    """
    init_db()
    inserted = 0
    skipped = 0

    with get_conn() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(
                    """
                    INSERT INTO transactions
                        (date, description, merchant_raw, amount, category, card, month)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(row.get("date", ""))[:10],
                        row.get("description", ""),
                        row.get("merchant_raw", ""),
                        float(row.get("amount", 0)),
                        row.get("category", "Uncategorized"),
                        row.get("card", ""),
                        row.get("month", ""),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

    return inserted, skipped


def load_transactions() -> pd.DataFrame:
    """Load all transactions from the database as a DataFrame."""
    init_db()
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC",
            conn,
        )
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def get_transaction_count() -> int:
    init_db()
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
    return row[0]


def clear_all_transactions():
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions")
