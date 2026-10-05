"""Tests for Multi-Bank Institutional Profiles and Synthetic Datasets."""

from decimal import Decimal

from app.evaluation.bank_profiles import (
    ALL_BANK_PROFILES,
    AMEX_PROFILE,
    CHASE_PROFILE,
    RBC_PROFILE,
    SCOTIABANK_PROFILE,
    TD_PROFILE,
    get_bank_profile_by_code,
)
from app.services.document_ai.categorizer import Categorizer
from app.services.document_ai.merchant_normalizer import MerchantNormalizer
from app.services.document_ai.parser import CSVParser


def test_bank_profiles_integrity():
    assert len(ALL_BANK_PROFILES) == 5
    codes = {p.institution_code for p in ALL_BANK_PROFILES}
    assert codes == {"RBC", "TD", "SCOTIA", "CHASE", "AMEX"}

    for profile in ALL_BANK_PROFILES:
        assert len(profile.transactions) >= 5
        assert profile.bank_name
        assert profile.currency in ("CAD", "USD")
        assert profile.account_type


def test_get_bank_profile_by_code():
    rbc = get_bank_profile_by_code("rbc")
    assert rbc is not None
    assert rbc.institution_code == "RBC"

    td = get_bank_profile_by_code("TD")
    assert td is not None
    assert td.bank_name == "TD Canada Trust"

    chase = get_bank_profile_by_code("Chase")
    assert chase is not None
    assert chase.currency == "USD"

    assert get_bank_profile_by_code("NONEXISTENT") is None


def test_rbc_csv_generation_and_parsing():
    csv_text = RBC_PROFILE.to_csv_string()
    csv_bytes = csv_text.encode("utf-8")
    candidates = CSVParser.parse(csv_bytes)

    assert len(candidates) == len(RBC_PROFILE.transactions)
    # Check first transaction (monthly fee)
    fee_cand = candidates[0]
    assert fee_cand.date.isoformat() == "2026-09-01"
    assert "MONTHLY ACCOUNT FEE" in fee_cand.original_description
    assert fee_cand.amount == Decimal("-16.95")

    # Check payroll deposit
    payroll_cand = candidates[1]
    assert payroll_cand.amount == Decimal("3450.00")


def test_td_csv_generation_and_parsing():
    csv_text = TD_PROFILE.to_csv_string()
    csv_bytes = csv_text.encode("utf-8")
    candidates = CSVParser.parse(csv_bytes)

    assert len(candidates) == len(TD_PROFILE.transactions)
    # Check FX conversion
    fx_cand = candidates[0]
    assert "AMZN MKTP" in fx_cand.original_description
    assert fx_cand.amount == Decimal("-61.43")

    # Check credit card payment deposit
    pay_cand = candidates[4]
    assert pay_cand.amount == Decimal("500.00")


def test_scotia_csv_generation_and_parsing():
    csv_text = SCOTIABANK_PROFILE.to_csv_string()
    csv_bytes = csv_text.encode("utf-8")
    candidates = CSVParser.parse(csv_bytes)

    assert len(candidates) == len(SCOTIABANK_PROFILE.transactions)
    cineplex = candidates[0]
    assert "CINEPLEX ODEON" in cineplex.original_description
    assert cineplex.amount == Decimal("-38.50")


def test_chase_csv_generation_and_parsing():
    csv_text = CHASE_PROFILE.to_csv_string()
    csv_bytes = csv_text.encode("utf-8")
    candidates = CSVParser.parse(csv_bytes)

    assert len(candidates) == len(CHASE_PROFILE.transactions)
    delta = candidates[0]
    assert "DELTA AIR LINES" in delta.original_description
    # Note: CSVParser extracts amount from Chase format
    assert abs(delta.amount) == Decimal("340.50")


def test_amex_csv_generation_and_parsing():
    csv_text = AMEX_PROFILE.to_csv_string()
    csv_bytes = csv_text.encode("utf-8")
    candidates = CSVParser.parse(csv_bytes)

    assert len(candidates) == len(AMEX_PROFILE.transactions)
    fee = candidates[0]
    assert "ANNUAL MEMBERSHIP FEE" in fee.original_description
    assert fee.amount == Decimal("-799.00")


def test_bank_transactions_ai_normalization_and_categorization():
    # Test normalization on sample descriptions from diverse banks
    norm, conf = MerchantNormalizer.normalize("TST* TIM HORTONS #4921 TORONTO ON")
    assert norm == "Tim Hortons"
    assert conf >= 0.8

    norm, conf = MerchantNormalizer.normalize("DELTA AIR LINES 0062491829 ATLANTA GA")
    assert norm == "Delta Air Lines"
    assert conf >= 0.8

    norm, conf = MerchantNormalizer.normalize("CINEPLEX ODEON YONGE & DUNDAS TORONTO ON")
    assert norm == "Cineplex"
    assert conf >= 0.8

    # Test categorization
    cat, subcat, conf, txn_type = Categorizer.classify(
        merchant="Tim Hortons",
        original_description="TST* TIM HORTONS #4921 TORONTO ON",
        amount=Decimal("-4.65"),
    )
    assert cat == "Food"
    assert txn_type == "expense"

    cat, subcat, conf, txn_type = Categorizer.classify(
        merchant="Delta Air Lines",
        original_description="DELTA AIR LINES 0062491829 ATLANTA GA",
        amount=Decimal("-340.50"),
    )
    assert cat == "Travel"
    assert txn_type == "expense"
