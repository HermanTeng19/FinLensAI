"""Multi-Bank Realistic Test Datasets & Diverse Institutional Profiles for FinLens AI.

Provides synthetic real-world statement datasets covering:
1. RBC (Royal Bank of Canada): Chequing fees, payroll deposit, Interac e-transfers, Tim Hortons.
2. TD Canada Trust: USD foreign exchange conversions, FX fees, credit card statements.
3. Scotiabank: Scene+ points, Cineplex entertainment, supermarket groceries.
4. Chase (US): USD credit card, Delta flights, Whole Foods, Spotify, Starbucks.
5. American Express: Travel charges, airline refunds, annual fee, fine dining.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SyntheticBankTransaction:
    date: str
    description: str
    amount: str
    currency: str
    expected_merchant: str
    expected_category: str
    expected_type: str
    is_recurring: bool = False
    is_fee: bool = False
    is_refund: bool = False
    is_foreign_currency: bool = False


@dataclass
class BankProfile:
    bank_name: str
    institution_code: str
    account_type: str
    currency: str
    statement_format: str
    transactions: list[SyntheticBankTransaction]

    def to_csv_string(self) -> str:
        """Generate a realistic raw CSV statement text matching the bank's format."""
        if self.institution_code == "RBC":
            lines = [
                "Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$",
            ]
            for t in self.transactions:
                lines.append(f'Chequing,00000-1234567,{t.date},,"{t.description}",,{t.amount}')
            return "\n".join(lines)

        elif self.institution_code == "TD":
            lines = [
                "Transaction Date,Description,Withdrawals,Deposits,Balance",
            ]
            for t in self.transactions:
                amt = Decimal(t.amount)
                if amt < 0:
                    lines.append(f'{t.date},"{t.description}",{abs(amt):.2f},,')
                else:
                    lines.append(f'{t.date},"{t.description}",,{amt:.2f},')
            return "\n".join(lines)

        elif self.institution_code == "SCOTIA":
            lines = [
                "Date,Transaction,Amount",
            ]
            for t in self.transactions:
                lines.append(f'{t.date},"{t.description}",{t.amount}')
            return "\n".join(lines)

        elif self.institution_code == "CHASE":
            lines = [
                "Transaction Date,Post Date,Description,Category,Type,Amount,Memo",
            ]
            for t in self.transactions:
                # Chase uses positive for charges, negative for payments/refunds
                amt = Decimal(t.amount)
                chase_amt = -amt
                lines.append(
                    f'{t.date},{t.date},"{t.description}",{t.expected_category},Sale,{chase_amt:.2f},'
                )
            return "\n".join(lines)

        elif self.institution_code == "AMEX":
            lines = [
                "Date,Description,Amount,Extended Details",
            ]
            for t in self.transactions:
                lines.append(f'{t.date},"{t.description}",{t.amount},Reference #928374829')
            return "\n".join(lines)

        else:
            lines = ["Date,Description,Amount,Currency"]
            for t in self.transactions:
                lines.append(f'{t.date},"{t.description}",{t.amount},{t.currency}')
            return "\n".join(lines)


# ===========================================================================
# 1. RBC Profile (Royal Bank of Canada)
# ===========================================================================
RBC_PROFILE = BankProfile(
    bank_name="Royal Bank of Canada",
    institution_code="RBC",
    account_type="Chequing",
    currency="CAD",
    statement_format="RBC_CSV",
    transactions=[
        SyntheticBankTransaction(
            date="2026-09-01",
            description="MONTHLY ACCOUNT FEE - SIGNATURE NO LIMIT",
            amount="-16.95",
            currency="CAD",
            expected_merchant="Royal Bank of Canada",
            expected_category="Finance",
            expected_type="expense",
            is_fee=True,
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-05",
            description="DIRECT DEP ACME CORP PAYROLL",
            amount="3450.00",
            currency="CAD",
            expected_merchant="Acme Corp",
            expected_category="Income",
            expected_type="income",
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-06",
            description="INTERAC E-TRF SENT TO JOHN DOE - RENT",
            amount="-1850.00",
            currency="CAD",
            expected_merchant="Interac e-Transfer",
            expected_category="Housing",
            expected_type="expense",
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-08",
            description="TST* TIM HORTONS #4921 TORONTO ON",
            amount="-4.65",
            currency="CAD",
            expected_merchant="Tim Hortons",
            expected_category="Food",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-12",
            description="METRO INC #149 TORONTO ON",
            amount="-78.40",
            currency="CAD",
            expected_merchant="Metro",
            expected_category="Food",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-15",
            description="INTERAC E-TRF RECD FROM SARAH DINNER SPLIT",
            amount="42.50",
            currency="CAD",
            expected_merchant="Interac e-Transfer",
            expected_category="Income",
            expected_type="income",
        ),
    ],
)


# ===========================================================================
# 2. TD Canada Trust Profile
# ===========================================================================
TD_PROFILE = BankProfile(
    bank_name="TD Canada Trust",
    institution_code="TD",
    account_type="Credit Card",
    currency="CAD",
    statement_format="TD_CSV",
    transactions=[
        SyntheticBankTransaction(
            date="2026-09-02",
            description="AMZN MKTP US*102948 SEATTLE WA USD 45.00 @ 1.3650",
            amount="-61.43",
            currency="CAD",
            expected_merchant="Amazon",
            expected_category="Shopping",
            expected_type="expense",
            is_foreign_currency=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-02",
            description="FOREIGN CURRENCY CONVERSION FEE 2.5%",
            amount="-1.54",
            currency="CAD",
            expected_merchant="TD Canada Trust",
            expected_category="Finance",
            expected_type="expense",
            is_fee=True,
            is_foreign_currency=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-07",
            description="NETFLIX.COM LOS GATOS CA",
            amount="-19.99",
            currency="CAD",
            expected_merchant="Netflix",
            expected_category="Subscriptions",
            expected_type="expense",
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-14",
            description="SHELL OIL 4910 MISSISSAUGA ON",
            amount="-65.20",
            currency="CAD",
            expected_merchant="Shell",
            expected_category="Transportation",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-20",
            description="PAYMENT - THANK YOU / PAIEMENT - MERCI",
            amount="500.00",
            currency="CAD",
            expected_merchant="Payment",
            expected_category="Finance",
            expected_type="transfer",
        ),
    ],
)


# ===========================================================================
# 3. Scotiabank Profile
# ===========================================================================
SCOTIABANK_PROFILE = BankProfile(
    bank_name="The Bank of Nova Scotia (Scotiabank)",
    institution_code="SCOTIA",
    account_type="Credit Card",
    currency="CAD",
    statement_format="SCOTIA_CSV",
    transactions=[
        SyntheticBankTransaction(
            date="2026-09-04",
            description="CINEPLEX ODEON YONGE & DUNDAS TORONTO ON",
            amount="-38.50",
            currency="CAD",
            expected_merchant="Cineplex",
            expected_category="Entertainment",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-09",
            description="SOBEYS #0294 EDMONTON AB",
            amount="-94.15",
            currency="CAD",
            expected_merchant="Sobeys",
            expected_category="Food",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-11",
            description="CINEPLEX STORE STREAMING TORONTO ON",
            amount="-6.99",
            currency="CAD",
            expected_merchant="Cineplex",
            expected_category="Entertainment",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-16",
            description="SCENE+ REWARDS REDEMPTION CREDIT",
            amount="20.00",
            currency="CAD",
            expected_merchant="Scotiabank",
            expected_category="Entertainment",
            expected_type="income",
            is_refund=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-18",
            description="UBER *TRIP TORONTO ON",
            amount="-22.40",
            currency="CAD",
            expected_merchant="Uber",
            expected_category="Transportation",
            expected_type="expense",
        ),
    ],
)


# ===========================================================================
# 4. Chase Profile (US Bank)
# ===========================================================================
CHASE_PROFILE = BankProfile(
    bank_name="JPMorgan Chase",
    institution_code="CHASE",
    account_type="Credit Card",
    currency="USD",
    statement_format="CHASE_CSV",
    transactions=[
        SyntheticBankTransaction(
            date="2026-09-03",
            description="DELTA AIR LINES 0062491829 ATLANTA GA",
            amount="-340.50",
            currency="USD",
            expected_merchant="Delta Air Lines",
            expected_category="Travel",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-05",
            description="WHOLE FOODS MKT 10293 NEW YORK NY",
            amount="-88.60",
            currency="USD",
            expected_merchant="Whole Foods",
            expected_category="Food",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-10",
            description="SPOTIFY USA NEW YORK NY",
            amount="-11.99",
            currency="USD",
            expected_merchant="Spotify",
            expected_category="Subscriptions",
            expected_type="expense",
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-12",
            description="STARBUCKS STORE 09182 SEATTLE WA",
            amount="-5.85",
            currency="USD",
            expected_merchant="Starbucks",
            expected_category="Food",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-25",
            description="AUTOMATIC PAYMENT - THANK YOU",
            amount="400.00",
            currency="USD",
            expected_merchant="Payment",
            expected_category="Finance",
            expected_type="transfer",
        ),
    ],
)


# ===========================================================================
# 5. American Express Profile
# ===========================================================================
AMEX_PROFILE = BankProfile(
    bank_name="American Express",
    institution_code="AMEX",
    account_type="Charge Card",
    currency="CAD",
    statement_format="AMEX_CSV",
    transactions=[
        SyntheticBankTransaction(
            date="2026-09-01",
            description="ANNUAL MEMBERSHIP FEE PLATINUM",
            amount="-799.00",
            currency="CAD",
            expected_merchant="American Express",
            expected_category="Finance",
            expected_type="expense",
            is_fee=True,
            is_recurring=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-08",
            description="AIR CANADA 014294829 MONTREAL QC",
            amount="-640.20",
            currency="CAD",
            expected_merchant="Air Canada",
            expected_category="Travel",
            expected_type="expense",
        ),
        SyntheticBankTransaction(
            date="2026-09-12",
            description="AIR CANADA REFUND / REMBOURSEMENT BAGGAGE FEE",
            amount="50.00",
            currency="CAD",
            expected_merchant="Air Canada",
            expected_category="Travel",
            expected_type="income",
            is_refund=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-17",
            description="ALINEA RESTAURANT CHICAGO IL",
            amount="-385.00",
            currency="USD",
            expected_merchant="Alinea",
            expected_category="Food",
            expected_type="expense",
            is_foreign_currency=True,
        ),
        SyntheticBankTransaction(
            date="2026-09-28",
            description="AMEX AUTOPAY PAYMENT RECEIVED",
            amount="1000.00",
            currency="CAD",
            expected_merchant="Payment",
            expected_category="Finance",
            expected_type="transfer",
        ),
    ],
)


# All Bank Profiles
ALL_BANK_PROFILES: list[BankProfile] = [
    RBC_PROFILE,
    TD_PROFILE,
    SCOTIABANK_PROFILE,
    CHASE_PROFILE,
    AMEX_PROFILE,
]


def get_bank_profile_by_code(code: str) -> BankProfile | None:
    """Retrieve bank profile by institution code."""
    for p in ALL_BANK_PROFILES:
        if p.institution_code.upper() == code.upper():
            return p
    return None
