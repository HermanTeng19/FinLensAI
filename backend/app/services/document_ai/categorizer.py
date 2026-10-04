from decimal import Decimal


class Categorizer:
    RULES = [
        # Income Rules
        ("Income", "Salary", ["PAYROLL", "SALARY", "DIRECT DEP", "EMPLOYER", "WAGES"]),
        ("Income", "Investment", ["DIVIDEND", "INTEREST PAID", "CASHBACK"]),
        # Transfer Rules
        ("Transfer", "e-Transfer", ["E-TRANSFER", "INTERAC", "EMAIL TRF"]),
        ("Transfer", "Card Payment", ["PAYMENT - THANK YOU", "CREDIT CARD PAYMENT", "AUTOPAY"]),
        # Food Delivery (Checked before Rideshare so UBER EATS matches before UBER)
        ("Food", "Food Delivery", ["UBER EATS", "DOORDASH", "SKIPTHEDISHES"]),
        # Transportation
        (
            "Transportation",
            "Public Transit",
            ["TRANSIT", "METRO PASS", "PRESTO", "COMPASS", "BUS", "TRAIN", "FERRY"],
        ),
        ("Transportation", "Rideshare", ["UBER", "LYFT", "TAXI", "CAB"]),
        (
            "Transportation",
            "Gas & Fuel",
            ["SHELL", "CHEVRON", "ESSO", "PETRO-CANADA", "GAS STATION", "EXXON"],
        ),
        ("Transportation", "Parking", ["PARKING", "IMPARK", "EASYPARK"]),
        # Food & Dining
        ("Food", "Coffee & Cafe", ["TIM HORTONS", "STARBUCKS", "CAFE", "COFFEE", "BAKERY"]),
        (
            "Food",
            "Restaurants",
            [
                "MCDONALD",
                "SUBWAY",
                "KFC",
                "CHIPOTLE",
                "RESTAURANT",
                "BISTRO",
                "GRILL",
                "PIZZA",
                "BURGER",
                "SUSHI",
                "KEG",
            ],
        ),
        (
            "Food",
            "Groceries",
            [
                "LOBLAWS",
                "SAFEWAY",
                "METRO",
                "SOBEYS",
                "WHOLE FOODS",
                "TRADER JOE",
                "SUPERMARKET",
                "GROCERY",
            ],
        ),
        # Shopping
        ("Shopping", "Online Shopping", ["AMAZON", "EBAY", "ALIEXPRESS"]),
        ("Shopping", "General Retail", ["WALMART", "COSTCO", "TARGET"]),
        ("Shopping", "Electronics", ["BEST BUY", "APPLE", "MICROSOFT"]),
        ("Shopping", "Home Goods", ["HOME DEPOT", "IKEA", "LOWE'S", "BED BATH"]),
        (
            "Shopping",
            "Software & Subscriptions",
            ["OPENAI", "CHATGPT", "GITHUB", "AWS", "ADOBE", "CANVA"],
        ),
        # Entertainment
        (
            "Entertainment",
            "Streaming",
            ["NETFLIX", "SPOTIFY", "DISNEY+", "YOUTUBE", "APPLE TV", "PRIME VIDEO"],
        ),
        ("Entertainment", "Gaming", ["STEAM", "PLAYSTATION", "XBOX", "NINTENDO"]),
        ("Entertainment", "Events & Movies", ["CINEMA", "THEATRE", "CONCERT", "TICKETMASTER"]),
        # Utilities
        (
            "Utilities",
            "Electricity & Gas",
            ["HYDRO", "BC HYDRO", "TORONTO HYDRO", "ENBRIDGE", "POWER", "ELECTRIC"],
        ),
        (
            "Utilities",
            "Internet & Mobile",
            ["TELUS", "ROGERS", "BELL", "FIDO", "KUDOO", "VERIZON", "AT&T", "INTERNET"],
        ),
        # Healthcare
        ("Healthcare", "Pharmacy", ["PHARMACY", "SHOPPERS DRUG", "REXALL", "CVS", "WALGREENS"]),
        ("Healthcare", "Medical & Dental", ["DENTAL", "CLINIC", "DOCTOR", "HOSPITAL", "OPTOMETRY"]),
        # Housing
        ("Housing", "Rent & Mortgage", ["RENT", "MORTGAGE", "CONDO FEE", "HOA"]),
        # Travel
        (
            "Travel",
            "Flights",
            ["AIR CANADA", "WESTJET", "UNITED AIRLINES", "DELTA", "AIRLINE", "FLIGHT"],
        ),
        ("Travel", "Lodging", ["HOTEL", "AIRBNB", "MARRIOTT", "HILTON"]),
        # Education
        (
            "Education",
            "Tuition & Courses",
            ["UNIVERSITY", "COLLEGE", "TUITION", "COURSERA", "UDEMY"],
        ),
        # Financial
        (
            "Financial",
            "Bank Fees",
            ["SERVICE CHARGE", "MONTHLY FEE", "OVERDRAFT", "ATM FEE", "ANNUAL FEE"],
        ),
    ]

    @classmethod
    def classify(
        cls, merchant: str, original_description: str, amount: Decimal
    ) -> tuple[str, str | None, float, str]:
        """
        Classifies transaction into (category, subcategory, confidence, transaction_type).
        """
        text_to_match = f"{merchant} {original_description}".upper()

        # Check Income first if amount is positive
        if amount > 0:
            for cat, subcat, keywords in cls.RULES:
                if cat in ("Income", "Transfer") and any(kw in text_to_match for kw in keywords):
                    txn_type = "income" if cat == "Income" else "transfer"
                    return cat, subcat, 0.96, txn_type
            # Fallback for positive amounts
            return "Income", "General Income", 0.85, "income"

        # Check Expense / Transfer rules for negative amounts
        for cat, subcat, keywords in cls.RULES:
            if any(kw in text_to_match for kw in keywords):
                txn_type = "transfer" if cat == "Transfer" else "expense"
                return cat, subcat, 0.95, txn_type

        # Fallback category
        return "Other", "Uncategorized", 0.70, "expense"
