"""
parse_apple_pdfs.py

Extracts transactions from Apple Card monthly PDF statements and writes
a single master CSV compatible with the dashboard's Apple Card parser.

Usage:
    python parse_apple_pdfs.py <folder_containing_pdfs> [output.csv]

Example:
    python parse_apple_pdfs.py data/apple_statements apple_card_history.csv
"""

import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

# Matches a transaction line:
#   03/13/2021  TST* B2 BISTRO + BAR ...  1%  $2.48  $248.18
TX_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+\d+%\s+\$[\d.]+\s+\$(\d[\d,]*\.\d{2})\s*$"
)

# Lines to skip inside the Transactions section
SKIP_PATTERNS = [
    re.compile(r"^Date\s+Description"),      # header row
    re.compile(r"Promo Daily Cash"),          # sub-row for some transactions
    re.compile(r"^Total Daily Cash"),         # section footer
    re.compile(r"^Total charges"),            # section footer
    re.compile(r"^If you have an iPhone"),    # footnote
]


def _should_skip(line: str) -> bool:
    return any(p.search(line) for p in SKIP_PATTERNS)


def parse_pdf(path: Path) -> list[dict]:
    transactions = []
    in_transactions = False

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                # Section boundaries
                if line == "Transactions":
                    in_transactions = True
                    continue
                if line in ("Payments", "Interest Charged", "Daily Cash", "Legal"):
                    in_transactions = False
                    continue

                if not in_transactions:
                    continue
                if _should_skip(line):
                    continue

                m = TX_RE.match(line)
                if m:
                    date, description, amount = m.groups()
                    transactions.append({
                        "Transaction Date": date,
                        "Description": description.strip(),
                        "Amount (USD)": float(amount.replace(",", "")),
                        "Type": "Purchase",
                    })

    return transactions


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_apple_pdfs.py <pdf_folder> [output.csv]")
        sys.exit(1)

    pdf_folder = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("apple_card_history.csv")

    pdfs = sorted(pdf_folder.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_folder}")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDFs...")

    all_transactions = []
    for pdf_path in pdfs:
        txns = parse_pdf(pdf_path)
        print(f"  {pdf_path.name}: {len(txns)} transactions")
        all_transactions.extend(txns)

    if not all_transactions:
        print("No transactions extracted.")
        sys.exit(1)

    df = pd.DataFrame(all_transactions)
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], format="%m/%d/%Y")
    df = df.sort_values("Transaction Date").reset_index(drop=True)
    df["Transaction Date"] = df["Transaction Date"].dt.strftime("%m/%d/%Y")

    df.to_csv(output_path, index=False)
    print(f"\nDone. {len(df)} total transactions saved to {output_path}")


if __name__ == "__main__":
    main()
