import re

# ── Known merchant mappings ───────────────────────────────────────────────────
# Checked before generic cleanup. Order matters — more specific first.
# (regex_pattern, clean_name)
MERCHANT_MAP = [
    # Shopping
    (r"AMZN|AMAZON", "Amazon"),
    (r"WHOLEFDS|WHOLE\s*FOODS", "Whole Foods"),
    (r"TRADER\s*JOE", "Trader Joe's"),
    (r"COSTCO", "Costco"),
    (r"WALMART|WAL-MART", "Walmart"),
    (r"TARGET", "Target"),
    (r"BEST\s*BUY", "Best Buy"),
    (r"HOME\s*DEPOT", "Home Depot"),
    (r"LOWE'?S", "Lowe's"),
    (r"IKEA", "IKEA"),
    (r"DOLLARTREE|DOLLAR\s*TREE", "Dollar Tree"),
    (r"GOODWILL", "Goodwill"),
    # Grocery
    (r"SUPER\s*FOOD", "Super Foodtown"),    # covers SUPER FOODTOWN + SUPER FOODTOW (truncated)
    (r"STOP\s*&\s*SHOP", "Stop & Shop"),
    (r"WELSH\s*FARMS", "Welsh Farms"),
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
    (r"APPLEBEE'?S|APPLEBEES", "Applebee's"),
    (r"TOO\s*GOOD\s*TO\s*GO", "Too Good to Go"),
    # Local NJ merchants
    (r"QUICK\s*CHEK|QUICKCHEK", "Quick Chek"),
    (r"WAWA\b", "Wawa"),
    (r"GATEWAY\s*BAR", "Gateway Bar & Liquor"),
    (r"SALTWATER\s*LIQ", "Saltwater Liquor"),
    (r"CIRCUS\s*WINES", "Circus Wines"),
    (r"PROVING\s*GROUND", "The Proving Ground"),
    (r"JASPAN\s*BROTHERS", "Jaspan Brothers"),
    (r"ATLANTIC\s*BAGEL", "Atlantic Bagel Cafe"),
    (r"CHUBBY\s*PICKLE", "The Chubby Pickle"),
    (r"DUBLIN\s*HOUSE", "The Dublin House"),
    (r"CHILANGOS", "Chilangos"),
    (r"BIGMIKES|BIG\s*MIKES", "Big Mike's"),
    (r"VILLA\s*RISTORANTE", "Villa Ristorante"),
    (r"LUCKY\s*DOG\s*SURF", "Lucky Dog Surf"),
    (r"GARDEN\s*STATE\s*CAR\s*WASH", "Garden State Car Wash"),
    (r"RAVE\b", "Rave Cinemas"),
    (r"SEASTREAK", "Seastreak"),
    (r"GALAXY\s*TOYOTA", "Galaxy Toyota"),
    (r"KALKOMEY", "Kalkomey"),
    # Transit
    (r"NJT\s*RAIL|NJT\s*BUS|NJ\s*TRANSIT", "NJ Transit"),
    (r"MTA\b|NYCT\s*PAYGO|MTA\*NYCT", "MTA"),
    (r"CANTEEN\s*VEND|USA\*CANTEEN", "Canteen Vending"),
    (r"MIDDLETOWN\s*TOWNSHIP", "Middletown Township"),
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
    (r"APPLE\s*SERVICES|APPLE\.COM/BILL|APPLE\.COM|APPLE\s*STORE", "Apple"),
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
    (r"CVS", "CVS"),
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
    # Finance
    (r"FOREIGN\s*TRANSACTION\s*FEE", "Foreign Transaction Fee"),
    (r"UBS\b", "UBS"),
    # Payments / peer-to-peer
    (r"VENMO", "Venmo"),
    (r"ZELLE", "Zelle"),
    (r"PAYPAL", "PayPal"),
    (r"CASH\s*APP|CASHAPP", "Cash App"),
]

# ── POS prefixes to strip ─────────────────────────────────────────────────────
_POS_PREFIXES = re.compile(
    r"^(SQ \*|TST\*|SP |PP\*|PAYPAL \*|VZWRLSS\*|SMB\*|AMEX\*|APLPAY\s*|AПЛPAY\s*)",
    re.IGNORECASE,
)

# ── Generic cleanup steps ─────────────────────────────────────────────────────
_AFTER_STAR    = re.compile(r"\*.*$")
_STORE_NUMBER  = re.compile(r"\s*#\d+")
_PHONE_NUMBER  = re.compile(r"\s+\d{10,}\s*")              # 10+ digit phone numbers
_STREET_ADDR   = re.compile(                                # "123 MAIN ST ... 07732 NJ USA"
    r"\s+\d{1,5}\s+(?:\w+\s+)*(?:ST|AVE|BLVD|RD|DR|LN|PL|WAY|PLAZA|PKWY|CT|HWY|HIGHWAY|ROUTE|RT)\b.*$",
    re.IGNORECASE,
)
_ZIP_ONWARDS   = re.compile(r"\s+\d{5}(?:-\d{4})?\s*\w*\s*$")  # trailing zip + country
_STATE_COUNTRY = re.compile(r"\s+[A-Z]{2}\s+USA\s*$")      # "NJ USA"
_TRAILING_DIGITS = re.compile(r"\s+\d{4,}$")
_LOCATION_DASH   = re.compile(r"\s+-\s+[A-Z\s,]+[A-Z]{2}$")
_LOCATION_COMMA  = re.compile(r"\s+[A-Z\s]+,\s*[A-Z]{2}$")
_DOMAIN_EXT      = re.compile(r"\.(COM|NET|ORG|IO|CO)\b.*$", re.IGNORECASE)


def clean_merchant(raw: str) -> str:
    if not raw or not isinstance(raw, str):
        return raw

    upper = raw.strip().upper()

    # 1. Check known merchants first (before any cleanup)
    for pattern, clean_name in MERCHANT_MAP:
        if re.search(pattern, upper):
            return clean_name

    # 2. Generic cleanup
    name = upper
    name = _POS_PREFIXES.sub("", name).strip()

    # Re-check known merchants after stripping prefix (e.g. "AplPay CHIPOTLE...")
    for pattern, clean_name in MERCHANT_MAP:
        if re.search(pattern, name):
            return clean_name

    name = _AFTER_STAR.sub("", name).strip()
    name = _PHONE_NUMBER.sub(" ", name).strip()
    name = _STREET_ADDR.sub("", name).strip()
    name = _ZIP_ONWARDS.sub("", name).strip()
    name = _STATE_COUNTRY.sub("", name).strip()
    name = _STORE_NUMBER.sub("", name).strip()
    name = _TRAILING_DIGITS.sub("", name).strip()
    name = _LOCATION_DASH.sub("", name).strip()
    name = _LOCATION_COMMA.sub("", name).strip()
    name = _DOMAIN_EXT.sub("", name).strip()

    return name.title() if name else raw.strip().title()
