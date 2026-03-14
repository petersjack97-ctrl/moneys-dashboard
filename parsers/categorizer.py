import re

# ── Normalize raw bank category strings to a standard set ────────────────────
#
# Chase categories:     Food & Drink, Shopping, Travel, Entertainment,
#                       Health & Wellness, Gas, Groceries, Personal,
#                       Home, Education, Automotive, Professional Services,
#                       Fees & Adjustments, Gifts & Donations, Bills & Utilities
#
# Amex categories:      Restaurant-Restaurant, Travel-Airline, Travel-Hotel,
#                       Travel-Car Rental, Merchandise & Supplies,
#                       Entertainment, Gas Stations, Supermarkets,
#                       Health & Wellness, Other
#
# Apple categories:     Food and Drinks, Shopping, Entertainment,
#                       Transportation, Health, Travel, Utilities, Other
#
# Standard categories we normalize everything to:
#   Food & Drink | Groceries | Shopping | Travel | Transportation |
#   Entertainment | Health & Wellness | Gas | Bills & Utilities |
#   Personal | Home | Education | Automotive | Fees & Adjustments |
#   Gifts & Donations | Business | Uncategorized

CATEGORY_MAP = {
    # Food & Drink
    "food & drink":         "Food & Drink",
    "food and drink":       "Food & Drink",
    "food and drinks":      "Food & Drink",
    "dining":               "Food & Drink",
    "restaurants":          "Food & Drink",
    "restaurant":           "Food & Drink",
    "restaurant-restaurant":"Food & Drink",
    "fast food":            "Food & Drink",
    "coffee":               "Food & Drink",
    "bars":                 "Food & Drink",
    # Groceries
    "groceries":            "Groceries",
    "supermarkets":         "Groceries",
    "supermarket":          "Groceries",
    # Shopping
    "shopping":             "Shopping",
    "merchandise & supplies":"Shopping",
    "merchandise and supplies":"Shopping",
    "clothing":             "Shopping",
    "electronics":          "Shopping",
    # Travel
    "travel":               "Travel",
    "travel-airline":       "Travel",
    "travel-hotel":         "Travel",
    "travel-car rental":    "Travel",
    "airline":              "Travel",
    "hotel":                "Travel",
    "lodging":              "Travel",
    "car rental":           "Travel",
    # Transportation
    "transportation":       "Transportation",
    "rideshare":            "Transportation",
    "taxi":                 "Transportation",
    "transit":              "Transportation",
    "parking":              "Transportation",
    "tolls":                "Transportation",
    # Entertainment
    "entertainment":        "Entertainment",
    "streaming":            "Entertainment",
    "movies":               "Entertainment",
    "music":                "Entertainment",
    "sports":               "Entertainment",
    # Health & Wellness
    "health & wellness":    "Health & Wellness",
    "health and wellness":  "Health & Wellness",
    "health":               "Health & Wellness",
    "medical":              "Health & Wellness",
    "pharmacy":             "Health & Wellness",
    "fitness":              "Health & Wellness",
    # Gas
    "gas":                  "Gas",
    "gas stations":         "Gas",
    "gas station":          "Gas",
    "fuel":                 "Gas",
    # Bills & Utilities
    "bills & utilities":    "Bills & Utilities",
    "bills and utilities":  "Bills & Utilities",
    "utilities":            "Bills & Utilities",
    "phone":                "Bills & Utilities",
    "internet":             "Bills & Utilities",
    "cable":                "Bills & Utilities",
    "insurance":            "Bills & Utilities",
    # Personal
    "personal":             "Personal",
    "personal care":        "Personal",
    "beauty":               "Personal",
    # Home
    "home":                 "Home",
    "home improvement":     "Home",
    "furniture":            "Home",
    # Education
    "education":            "Education",
    "tuition":              "Education",
    "books":                "Education",
    # Automotive
    "automotive":           "Automotive",
    "auto":                 "Automotive",
    "car":                  "Automotive",
    # Fees
    "fees & adjustments":   "Fees & Adjustments",
    "fees and adjustments": "Fees & Adjustments",
    "fees":                 "Fees & Adjustments",
    "bank fees":            "Fees & Adjustments",
    # Gifts & Donations
    "gifts & donations":    "Gifts & Donations",
    "gifts and donations":  "Gifts & Donations",
    "charity":              "Gifts & Donations",
    "donations":            "Gifts & Donations",
    # Business
    "business":             "Business",
    "professional services":"Business",
    "office":               "Business",
}

# ── Fallback: infer category from cleaned merchant name ──────────────────────
# Only used when bank CSV has no category or category is "Uncategorized"/"Other"
MERCHANT_CATEGORY_MAP = [
    # Food & Drink
    (r"Starbucks|Dunkin|Coffee|Cafe|Bakery", "Food & Drink"),
    (r"McDonald'?s|Burger King|Wendy'?s|Chick-fil-A|Taco Bell|Subway|Chipotle|Panera|Five Guys|Sweetgreen|Domino'?s|Pizza Hut", "Food & Drink"),
    (r"Uber Eats|DoorDash|Grubhub|Instacart", "Food & Drink"),
    (r"Restaurant|Sushi|Ramen|Grill|Diner|Kitchen|Bistro|Tavern|Bar\b|Pub\b|Brewery", "Food & Drink"),
    # Groceries
    (r"Whole Foods|Trader Joe'?s|Costco|Safeway|Kroger|Publix|Albertsons|Stop & Shop|Wegmans|Aldi|Lidl|Sprouts", "Groceries"),
    (r"Grocery|Supermarket|Market\b", "Groceries"),
    # Shopping
    (r"Amazon|Walmart|Target|Best Buy|Home Depot|Lowe'?s|IKEA|Macy'?s|Nordstrom|TJ Maxx|Marshalls|Gap|H&M|Zara|Nike|Adidas", "Shopping"),
    (r"Etsy|eBay|Shopify", "Shopping"),
    # Transportation
    (r"Uber$|Lyft", "Transportation"),
    (r"MTA|BART|Metro|Transit|Bus\b|Train\b|Amtrak", "Transportation"),
    (r"Parking|EZPass|SunPass|FastTrak", "Transportation"),
    # Travel
    (r"Delta|American Airlines|United Airlines|Southwest|JetBlue|Spirit Airlines", "Travel"),
    (r"Airbnb|Marriott|Hilton|Hyatt|IHG Hotels|Hotel\b|Motel\b", "Travel"),
    (r"Expedia|Booking|Hotels\.com|Kayak", "Travel"),
    # Entertainment
    (r"Netflix|Spotify|Hulu|Disney\+|Max \(HBO\)|Peacock|Paramount\+|YouTube|Apple", "Entertainment"),
    (r"Cinema|Theater|Theatre|AMC|Regal|Concert|Ticketmaster|StubHub", "Entertainment"),
    # Health & Wellness
    (r"CVS|Walgreens|Rite Aid|Pharmacy", "Health & Wellness"),
    (r"Gym|Planet Fitness|Equinox|SoulCycle|Peloton|Yoga", "Health & Wellness"),
    (r"Doctor|Dentist|Clinic|Hospital|Medical|Health", "Health & Wellness"),
    # Gas
    (r"Shell|ExxonMobil|Chevron|BP\b|Sunoco|Texaco|Citgo|Marathon|Speedway|Mobil", "Gas"),
    # Bills & Utilities
    (r"Verizon|AT&T|T-Mobile|Comcast|Xfinity|Spectrum|Google Fi", "Bills & Utilities"),
    (r"Electric|Water\b|Gas Bill|PG&E|ConEd|Duke Energy", "Bills & Utilities"),
    # Business
    (r"OpenAI|GitHub|Microsoft|Google|Notion|Dropbox|Slack|Zoom|Adobe", "Business"),
    # Personal
    (r"Venmo|Cash App|Zelle|PayPal", "Personal"),
]


def normalize_category(raw_category: str, merchant_name: str = "") -> str:
    """
    Normalize a raw bank category string to our standard set.
    Falls back to merchant-based inference if category is missing/generic.
    """
    if raw_category and raw_category.strip().lower() not in ("", "uncategorized", "other", "nan"):
        key = raw_category.strip().lower()
        # Direct map
        if key in CATEGORY_MAP:
            return CATEGORY_MAP[key]
        # Partial match (e.g. "Travel-Car Rental" → "Travel")
        for map_key, standard in CATEGORY_MAP.items():
            if map_key in key:
                return standard

    # Fallback: infer from merchant name
    if merchant_name:
        for pattern, category in MERCHANT_CATEGORY_MAP:
            if re.search(pattern, merchant_name, re.IGNORECASE):
                return category

    return "Uncategorized"
