"""
Transaction loading and filtering service for BillShield.
"""

import csv
import logging
from datetime import datetime, date
from typing import List, Optional, Union, Tuple
import pandas as pd
from pydantic import ValidationError

from backend.models.schemas import Transaction

logger = logging.getLogger(__name__)


def parse_date_safe(val: Union[str, date, datetime]) -> Optional[date]:
    """Safely parse date values into a datetime.date object."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if not val or not isinstance(val, str):
        return None
    
    val_str = val.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_float_safe(val: Union[str, float, int]) -> Optional[float]:
    """Safely parse numeric amounts into floats."""
    if val is None:
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def load_transactions(
    source: Union[str, pd.DataFrame],
    raise_on_error: bool = False
) -> Tuple[List[Transaction], List[str]]:
    """
    Loads, validates, and cleans transaction data from a CSV path or DataFrame.
    
    Returns:
        Tuple of (valid_transactions_list, list_of_warning_messages)
    """
    valid_transactions: List[Transaction] = []
    errors: List[str] = []
    seen_ids = set()

    if isinstance(source, str):
        try:
            df = pd.read_csv(source)
        except FileNotFoundError:
            err = f"Transaction CSV file not found at: {source}"
            errors.append(err)
            if raise_on_error:
                raise FileNotFoundError(err)
            return [], errors
        except Exception as e:
            err = f"Failed to parse CSV file at {source}: {str(e)}"
            errors.append(err)
            if raise_on_error:
                raise ValueError(err)
            return [], errors
    elif isinstance(source, pd.DataFrame):
        df = source
    else:
        err = f"Unsupported source type for load_transactions: {type(source)}"
        errors.append(err)
        if raise_on_error:
            raise TypeError(err)
        return [], errors

    required_cols = {"transaction_id", "date", "merchant", "amount"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        err = f"Missing required columns in dataset: {missing_cols}"
        errors.append(err)
        if raise_on_error:
            raise ValueError(err)
        return [], errors

    for idx, row in df.iterrows():
        tx_id_raw = row.get("transaction_id")
        if pd.isna(tx_id_raw) or not str(tx_id_raw).strip():
            errors.append(f"Row {idx}: missing transaction_id")
            continue
        
        tx_id = str(tx_id_raw).strip()
        if tx_id in seen_ids:
            errors.append(f"Row {idx}: duplicate transaction_id '{tx_id}' skipped")
            continue

        tx_date = parse_date_safe(row.get("date"))
        if not tx_date:
            errors.append(f"Row {idx} (ID '{tx_id}'): invalid or missing date '{row.get('date')}'")
            continue

        merchant_raw = row.get("merchant")
        if pd.isna(merchant_raw) or not str(merchant_raw).strip():
            errors.append(f"Row {idx} (ID '{tx_id}'): missing merchant name")
            continue
        merchant = str(merchant_raw).strip()

        amount = parse_float_safe(row.get("amount"))
        if amount is None or amount < 0:
            errors.append(f"Row {idx} (ID '{tx_id}'): invalid amount '{row.get('amount')}'")
            continue

        category = str(row.get("category", "Other")).strip() if not pd.isna(row.get("category")) else "Other"
        payment_method = str(row.get("payment_method", "Card")).strip() if not pd.isna(row.get("payment_method")) else "Card"
        description = str(row.get("description", "")).strip() if not pd.isna(row.get("description")) else ""

        try:
            tx = Transaction(
                transaction_id=tx_id,
                date=tx_date,
                merchant=merchant,
                amount=amount,
                category=category,
                payment_method=payment_method,
                description=description
            )
            valid_transactions.append(tx)
            seen_ids.add(tx_id)
        except ValidationError as ve:
            errors.append(f"Row {idx} (ID '{tx_id}'): validation error - {ve}")

    return valid_transactions, errors


def get_transactions(
    transactions: List[Transaction],
    merchant: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Transaction]:
    """Filters transactions based on query criteria."""
    filtered = transactions
    if merchant:
        merchant_lower = merchant.lower()
        filtered = [t for t in filtered if merchant_lower in t.merchant.lower()]
    if category:
        category_lower = category.lower()
        filtered = [t for t in filtered if category_lower in t.category.lower()]
    if start_date:
        filtered = [t for t in filtered if t.date >= start_date]
    if end_date:
        filtered = [t for t in filtered if t.date <= end_date]
    return filtered
