import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from pypdf import PdfReader


@dataclass
class ExtractedTransactionCandidate:
    date: date
    original_description: str
    amount: Decimal
    currency: str = "CAD"
    source_page: int | None = None


class DateParser:
    DATE_PATTERNS = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%d %b %Y",
        "%b %d %Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
    ]

    @classmethod
    def parse(cls, date_str: str, default_year: int = 2026) -> date | None:
        cleaned = date_str.strip()
        for fmt in cls.DATE_PATTERNS:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        # Try matching format like "Sep 18" or "09/18" with assumed year
        short_formats = [("%b %d", "%b %d %Y"), ("%m/%d", "%m/%d/%Y")]
        for short_fmt, full_fmt in short_formats:
            try:
                dt = datetime.strptime(f"{cleaned} {default_year}", full_fmt)
                return dt.date()
            except ValueError:
                continue

        return None


class AmountParser:
    @classmethod
    def parse(cls, amount_str: str) -> Decimal | None:
        cleaned = amount_str.strip()
        if not cleaned:
            return None

        # Detect suffix DR / CR
        is_dr = False
        is_cr = False
        if cleaned.upper().endswith("DR"):
            is_dr = True
            cleaned = cleaned[:-2].strip()
        elif cleaned.upper().endswith("CR"):
            is_cr = True
            cleaned = cleaned[:-2].strip()

        # Handle parentheses for negative numbers, e.g. (124.30)
        is_parenthesized = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            is_parenthesized = True
            cleaned = cleaned[1:-1].strip()

        # Remove currency symbols and commas
        cleaned = re.sub(r"[^\d.-]", "", cleaned)
        if not cleaned or cleaned == "-" or cleaned == ".":
            return None

        try:
            val = Decimal(cleaned)
            if is_parenthesized or is_dr:
                val = -abs(val)
            elif is_cr:
                val = abs(val)
            return val
        except InvalidOperation:
            return None


class CSVParser:
    DATE_HEADERS = {
        "date",
        "trans date",
        "posting date",
        "transaction date",
        "txn date",
        "post date",
    }
    DESC_HEADERS = {
        "description",
        "desc",
        "memo",
        "details",
        "payee",
        "narrative",
        "transaction",
        "description 1",
    }
    AMOUNT_HEADERS = {"amount", "total", "net amount", "value", "cad$", "usd$"}
    DEBIT_HEADERS = {"debit", "withdrawal", "withdrawals", "charge", "spent"}
    CREDIT_HEADERS = {"credit", "deposit", "deposits", "payment", "received"}

    @classmethod
    def parse(cls, content: bytes) -> list[ExtractedTransactionCandidate]:
        text_stream = io.StringIO(content.decode("utf-8-sig", errors="replace"))
        reader = csv.reader(text_stream)

        rows = [row for row in reader if row and any(field.strip() for field in row)]
        if not rows:
            return []

        # Find header row
        header_idx = -1
        col_map = {}

        for idx, row in enumerate(rows[:10]):
            normalized_row = [cell.strip().lower() for cell in row]
            has_date = any(c in cls.DATE_HEADERS for c in normalized_row)
            has_desc = any(c in cls.DESC_HEADERS for c in normalized_row)
            has_amount = any(
                c in cls.AMOUNT_HEADERS or c in cls.DEBIT_HEADERS or c in cls.CREDIT_HEADERS
                for c in normalized_row
            )

            if has_date and (has_desc or has_amount):
                header_idx = idx
                for col_i, cell in enumerate(normalized_row):
                    if cell in cls.DATE_HEADERS:
                        if "date" not in col_map or cell in ("date", "transaction date"):
                            col_map["date"] = col_i
                    elif cell in cls.DESC_HEADERS:
                        if "desc" not in col_map or cell in ("description", "desc", "payee"):
                            col_map["desc"] = col_i
                    elif cell in cls.AMOUNT_HEADERS:
                        if "amount" not in col_map or cell in ("amount", "total"):
                            col_map["amount"] = col_i
                    elif cell in cls.DEBIT_HEADERS:
                        if "debit" not in col_map:
                            col_map["debit"] = col_i
                    elif cell in cls.CREDIT_HEADERS:
                        if "credit" not in col_map:
                            col_map["credit"] = col_i
                break

        candidates: list[ExtractedTransactionCandidate] = []

        data_rows = rows[header_idx + 1 :] if header_idx != -1 else rows

        for row_num, row in enumerate(data_rows, start=1):
            if len(row) < 2:
                continue

            parsed_date: date | None = None
            description: str = ""
            amount: Decimal | None = None

            if "date" in col_map and col_map["date"] < len(row):
                parsed_date = DateParser.parse(row[col_map["date"]])
            if "desc" in col_map and col_map["desc"] < len(row):
                description = row[col_map["desc"]].strip()

            if "amount" in col_map and col_map["amount"] < len(row):
                amount = AmountParser.parse(row[col_map["amount"]])
            elif "debit" in col_map or "credit" in col_map:
                debit_val = (
                    AmountParser.parse(row[col_map["debit"]])
                    if "debit" in col_map and col_map["debit"] < len(row)
                    else None
                )
                credit_val = (
                    AmountParser.parse(row[col_map["credit"]])
                    if "credit" in col_map and col_map["credit"] < len(row)
                    else None
                )

                if debit_val and debit_val != Decimal(0):
                    amount = -abs(debit_val)
                elif credit_val and credit_val != Decimal(0):
                    amount = abs(credit_val)

            # Fallback heuristic if no header row detected
            if parsed_date is None or amount is None:
                for cell in row:
                    if parsed_date is None:
                        d = DateParser.parse(cell)
                        if d:
                            parsed_date = d
                            continue
                    if amount is None:
                        a = AmountParser.parse(cell)
                        if a is not None and "." in cell:
                            amount = a
                            continue
                    if not description and len(cell.strip()) > 3 and not DateParser.parse(cell):
                        description = cell.strip()

            if parsed_date and amount is not None and description:
                candidates.append(
                    ExtractedTransactionCandidate(
                        date=parsed_date,
                        original_description=description,
                        amount=amount,
                        source_page=1,
                    )
                )

        return candidates


class PDFParser:
    # Regex to identify typical bank statement lines:
    # Date (e.g. 2026-09-18 or 09/18/2026 or Sep 18, 2026) + Description + Amount (e.g. -124.30 or $124.30)
    TXN_LINE_PATTERN = re.compile(
        r"^(?P<date>\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|[A-Za-z]{3}\s+\d{1,2}(?:,?\s+\d{4})?)\s+"
        r"(?P<desc>.+?)\s+"
        r"(?P<amount>-?\$?\(?\d{1,3}(?:,\d{3})*\.\d{2}\)?(?:\s*(?:CR|DR))?)\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, content: bytes) -> list[ExtractedTransactionCandidate]:
        stream = io.BytesIO(content)
        reader = PdfReader(stream)
        candidates: list[ExtractedTransactionCandidate] = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                match = cls.TXN_LINE_PATTERN.match(line)
                if match:
                    d_str = match.group("date")
                    desc = match.group("desc").strip()
                    amt_str = match.group("amount")

                    parsed_date = DateParser.parse(d_str)
                    parsed_amount = AmountParser.parse(amt_str)

                    if parsed_date and parsed_amount is not None and desc:
                        candidates.append(
                            ExtractedTransactionCandidate(
                                date=parsed_date,
                                original_description=desc,
                                amount=parsed_amount,
                                source_page=page_num,
                            )
                        )

        return candidates
