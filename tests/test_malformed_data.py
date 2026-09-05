"""
Tests for error handling and malformed transaction records.
"""

import pandas as pd
from backend.services.transactions import load_transactions


def test_malformed_transaction_data_handled_safely():
    """Test 9: Verify malformed transaction data is handled safely without crashing."""
    df = pd.DataFrame([
        # Valid row 1
        {
            "transaction_id": "T001",
            "date": "2026-06-01",
            "merchant": "Netflix",
            "amount": "649.0",
            "category": "Subscription",
            "payment_method": "Card",
            "description": "Valid row",
        },
        # Duplicate transaction_id T001
        {
            "transaction_id": "T001",
            "date": "2026-06-02",
            "merchant": "Netflix",
            "amount": "649.0",
            "category": "Subscription",
            "payment_method": "Card",
            "description": "Duplicate ID",
        },
        # Invalid date
        {
            "transaction_id": "T002",
            "date": "invalid-date-format",
            "merchant": "Spotify",
            "amount": "119.0",
            "category": "Subscription",
            "payment_method": "AutoPay",
            "description": "Invalid date",
        },
        # Invalid amount
        {
            "transaction_id": "T003",
            "date": "2026-06-03",
            "merchant": "Adobe",
            "amount": "not_a_number",
            "category": "Subscription",
            "payment_method": "Card",
            "description": "Non-numeric amount",
        },
        # Missing merchant
        {
            "transaction_id": "T004",
            "date": "2026-06-04",
            "merchant": "",
            "amount": "299.0",
            "category": "Subscription",
            "payment_method": "Card",
            "description": "Missing merchant",
        },
        # Valid row 2
        {
            "transaction_id": "T005",
            "date": "2026-06-05",
            "merchant": "Amazon Prime",
            "amount": 299.0,
            "category": "Subscription",
            "payment_method": "AutoPay",
            "description": "Valid row 2",
        },
    ])

    transactions, errors = load_transactions(df)

    # Should safely load valid rows (T001 and T005) and log errors for malformed ones
    assert len(transactions) == 2
    assert transactions[0].transaction_id == "T001"
    assert transactions[1].transaction_id == "T005"
    assert len(errors) >= 4  # Errors logged for duplicate, date, amount, merchant
