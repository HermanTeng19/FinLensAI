import re

KNOWN_MERCHANTS = {
    "AMAZON": "Amazon",
    "AMZN": "Amazon",
    "APPLE": "Apple",
    "TIM HORTONS": "Tim Hortons",
    "TIM HORTON": "Tim Hortons",
    "STARBUCKS": "Starbucks",
    "COSTCO": "Costco",
    "WALMART": "Walmart",
    "UBER EATS": "Uber Eats",
    "UBER": "Uber",
    "LYFT": "Lyft",
    "NETFLIX": "Netflix",
    "SPOTIFY": "Spotify",
    "DISNEY": "Disney+",
    "YOUTUBE": "YouTube",
    "DOORDASH": "DoorDash",
    "SKIPTHEDISHES": "SkipTheDishes",
    "SHELL": "Shell",
    "CHEVRON": "Chevron",
    "ESSO": "Esso",
    "PETRO-CANADA": "Petro-Canada",
    "PETRO CANADA": "Petro-Canada",
    "LOBLAWS": "Loblaws",
    "SAFEWAY": "Safeway",
    "METRO": "Metro",
    "SOBEYS": "Sobeys",
    "WHOLE FOODS": "Whole Foods",
    "TRADER JOE": "Trader Joe's",
    "HOME DEPOT": "Home Depot",
    "IKEA": "IKEA",
    "BEST BUY": "Best Buy",
    "HYDRO": "Electric Utility",
    "BC HYDRO": "BC Hydro",
    "TORONTO HYDRO": "Toronto Hydro",
    "ENBRIDGE": "Enbridge Gas",
    "TELUS": "Telus",
    "ROGERS": "Rogers",
    "BELL": "Bell",
    "PAYROLL": "Payroll / Salary",
    "DIRECT DEP": "Direct Deposit",
    "SALARY": "Payroll / Salary",
    "E-TRANSFER": "Interac e-Transfer",
    "INTERAC": "Interac e-Transfer",
    "MCDONALD": "McDonald's",
    "MCDONALDS": "McDonald's",
    "SUBWAY": "Subway",
    "SHOPPERS DRUG": "Shoppers Drug Mart",
    "SHOPPERS": "Shoppers Drug Mart",
    "REXALL": "Rexall",
    "CVS": "CVS",
    "WALGREENS": "Walgreens",
    "AIR CANADA": "Air Canada",
    "WESTJET": "WestJet",
    "DELTA AIR LINES": "Delta Air Lines",
    "DELTA AIR": "Delta Air Lines",
    "DELTA": "Delta Air Lines",
    "CINEPLEX": "Cineplex",
    "ALINEA": "Alinea",
    "AIRBNB": "Airbnb",
    "EXPEDIA": "Expedia",
    "STEAM": "Steam",
    "PLAYSTATION": "PlayStation",
    "NINTENDO": "Nintendo",
    "MICROSOFT": "Microsoft",
    "GOOGLE": "Google",
    "OPENAI": "OpenAI",
    "CHATGPT": "OpenAI",
    "GITHUB": "GitHub",
}

SORTED_MERCHANT_KEYS = sorted(KNOWN_MERCHANTS.keys(), key=len, reverse=True)

# Prefixes to strip
PREFIX_REGEX = re.compile(
    r"^(?:TST\*|SQ\s*\*|SP\s*\*|PAYPAL\s*\*|GOOGLE\s*\*|STRIPE\s*\*|FSP\*)\s*",
    re.IGNORECASE,
)

# Suffixes to strip
SUFFIX_REGEX = re.compile(
    r"(?:\s*#\d+|\s+STORE\s+\d+|\s*\*\d+|\s+(?:VANCOUVER|TORONTO|MONTREAL|CALGARY|EDMONTON|OTTAWA)\s+[A-Z]{2}|\s+(?:BC|ON|AB|QC|MB|SK|NS|NB|NL|PE|CA|US)\b|\s+ONLINE|\s+PENDING|\.COM|\s+\d{6,})+$",
    re.IGNORECASE,
)


class MerchantNormalizer:
    @classmethod
    def normalize(cls, raw_description: str) -> tuple[str, float]:
        raw = raw_description.strip()
        if not raw:
            return "Unknown Merchant", 0.3

        # Normalize special separators (*, -, _, .) to spaces for robust keyword matching
        cleaned_spaces = re.sub(r"[*_\-./]+", " ", raw).upper()
        cleaned_spaces = re.sub(r"\s+", " ", cleaned_spaces).strip()

        # Step 1: Check known merchant keywords (longer first to match UBER EATS before UBER)
        for key in SORTED_MERCHANT_KEYS:
            pattern = r"(?:\b|^)" + re.escape(key) + r"(?:\b|$)"
            if re.search(pattern, cleaned_spaces):
                return KNOWN_MERCHANTS[key], 0.98

        # Step 2: Strip known noisy transaction gateway prefixes
        cleaned = PREFIX_REGEX.sub("", raw).strip()

        # Step 3: Strip noisy store IDs and location suffixes
        cleaned = SUFFIX_REGEX.sub("", cleaned).strip()

        upper_cleaned = cleaned.upper()

        # Step 4: Substring dictionary lookup
        for key in SORTED_MERCHANT_KEYS:
            if key in upper_cleaned:
                return KNOWN_MERCHANTS[key], 0.95

        # Step 5: Fallback title case normalization
        fallback_merchant = cleaned.title() if cleaned else raw.title()
        return fallback_merchant, 0.85
