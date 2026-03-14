import re

# ── Known merchant mappings ───────────────────────────────────────────────────
# Checked before generic cleanup. Order matters — more specific first.
# (regex_pattern, clean_name)
MERCHANT_MAP = [
    # Shopping
    (r"AMZN|AMAZON", "Amazon"),
    (r"WHOLE\s*FOODS", "Whole Foods"),
    (r"TRADER\s*JOE", "Trader Joe's"),
    (r"COSTCO", "Costco"),
    (r"WALMART|WAL-MART", "Walmart"),
    (r"TARGET", "Target"),
    (r"BEST\s*BUY", "Best Buy"),
    (r"HOME\s*DEPOT", "Home Depot"),
    (r"LOWE'?S", "Lowe's"),
    (r"IKEA", "IKEA"),
    # Food & drink
    (r"STARBUCKS", "Starbucks"),
    (r"DUNKIN", "Dunkin'"),
    (r"MCDONALD'?S|MCDONALDS", "McDonald's"),
    (r"CHICK.FIL.A|CHICKFILA", "Chick-fil-A"),
    (r"CHIPOTLE", "Chipotle"),
    (r"SUBWAY", "Subway"),
    (r"PANERA", "Panera Bread"),
    (r"DOMINO'?S", "Domino's"),
    (r"PIZZA\s*HUT", "Pizza Hut"),
    (r"TACO\s*BELL", "Taco Bell"),
    (r"WENDY'?S", "Wendy's"),
    (r"BURGER\s*KING", "Burger King"),
    (r"FIVE\s*GUYS", "Five Guys"),
    (r"SWEETGREEN", "Sweetgreen"),
    # Delivery
    (r"UBER.*EATS|UBEREATS", "Uber Eats"),
    (r"DOORDASH", "DoorDash"),
    (r"GRUBHUB", "Grubhub"),
    (r"INSTACART", "Instacart"),
    # Rideshare
    (r"UBER", "Uber"),
    (r"LYFT", "Lyft"),
    # Streaming & subscriptions
    (r"NETFLIX", "Netflix"),
    (r"SPOTIFY", "Spotify"),
    (r"HULU", "Hulu"),
    (r"DISNEY\+|DISNEYPLUS|DISNEY\s*PLUS", "Disney+"),
    (r"HBO|MAX\.COM", "Max (HBO)"),
    (r"PEACOCK", "Peacock"),
    (r"PARAMOUNT", "Paramount+"),
    (r"APPLE\.COM/BILL|APPLE\.COM|APPLE\s*STORE", "Apple"),
    (r"PRIME\s*VIDEO|AMAZON\s*VIDEO", "Amazon Prime Video"),
    (r"YOUTUBE", "YouTube"),
    # Tech & software
    (r"GOOGLE", "Google"),
    (r"MICROSOFT|MSFT", "Microsoft"),
    (r"OPENAI|CHATGPT", "OpenAI"),
    (r"GITHUB", "GitHub"),
    (r"DROPBOX", "Dropbox"),
    (r"NOTION", "Notion"),
    # Pharmacy & health
    (r"CVS/PHARMACY|CVS", "CVS"),
    (r"WALGREENS", "Walgreens"),
    (r"RITE\s*AID", "Rite Aid"),
    # Gas & auto
    (r"SHELL", "Shell"),
    (r"EXXON|MOBIL", "ExxonMobil"),
    (r"CHEVRON", "Chevron"),
    (r"BP\b", "BP"),
    (r"SUNOCO", "Sunoco"),
    # Travel
    (r"AIRBNB", "Airbnb"),
    (r"DELTA", "Delta Airlines"),
    (r"AMERICAN\s*AIRLINES|AA\.COM", "American Airlines"),
    (r"UNITED\s*AIRLINES|UNITED\.COM", "United Airlines"),
    (r"SOUTHWEST", "Southwest Airlines"),
    (r"JETBLUE", "JetBlue"),
    (r"SPIRIT\s*AIRLINES", "Spirit Airlines"),
    (r"MARRIOTT", "Marriott"),
    (r"HILTON", "Hilton"),
    (r"HYATT", "Hyatt"),
    (r"IHG|HOLIDAY\s*INN", "IHG Hotels"),
    # Payments / peer-to-peer (usually want to exclude from expenses)
    (r"VENMO", "Venmo"),
    (r"ZELLE", "Zelle"),
    (r"PAYPAL", "PayPal"),
    (r"CASH\s*APP|CASHAPP", "Cash App"),
]

# ── POS prefixes to strip ─────────────────────────────────────────────────────
_POS_PREFIXES = re.compile(
    r"^(SQ \*|TST\*|SP |PP\*|PAYPAL \*|VZWRLSS\*|SMB\*|AMEX\*)",
    re.IGNORECASE,
)

# ── Generic cleanup steps (applied when no known merchant matched) ────────────
_AFTER_STAR = re.compile(r"\*.*$")                         # drop everything after *
_STORE_NUMBER = re.compile(r"\s*#\d+")                     # strip #1234
_TRAILING_DIGITS = re.compile(r"\s+\d{4,}$")              # strip trailing 4+ digit codes
_LOCATION_DASH = re.compile(r"\s+-\s+[A-Z\s,]+[A-Z]{2}$") # " - SAN FRANCISCO CA"
_LOCATION_COMMA = re.compile(r"\s+[A-Z\s]+,\s*[A-Z]{2}$") # "SAN FRANCISCO, CA"
_DOMAIN_EXT = re.compile(r"\.(COM|NET|ORG|IO|CO)\b.*$", re.IGNORECASE)


def clean_merchant(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        return raw

    upper = raw.strip().upper()

    # 1. Check known merchants first
    for pattern, clean_name in MERCHANT_MAP:
        if re.search(pattern, upper):
            return clean_name

    # 2. Generic cleanup
    name = raw.strip().upper()
    name = _POS_PREFIXES.sub("", name).strip()
    name = _AFTER_STAR.sub("", name).strip()
    name = _STORE_NUMBER.sub("", name).strip()
    name = _TRAILING_DIGITS.sub("", name).strip()
    name = _LOCATION_DASH.sub("", name).strip()
    name = _LOCATION_COMMA.sub("", name).strip()
    name = _DOMAIN_EXT.sub("", name).strip()

    # 3. Title-case the result
    return name.title() if name else raw.strip().title()
