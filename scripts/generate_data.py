"""
Synthetic Financial Dataset Generator for BillShield.

Generates realistic household transaction data (~1000+ transactions) across 12 months
with 14 recurring subscriptions containing all benchmark hackathon scenarios:
- Normal recurring subscriptions
- Price increases (Netflix ₹649 -> ₹799, NewsPlus ₹199 -> ₹249)
- Potentially unused subscriptions (FitnessPro 91d, GamingPlus 105d)
- Upcoming renewals (Adobe 5d, Dropbox 3d, CloudBox 12d)
- Overlapping services (Cloud Storage: Dropbox, Google One, CloudBox)
"""

import os
import random
import csv
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


def generate_dataset(
    output_dir: str = "backend/data",
    start_date_str: str = "2025-09-01",
    end_date_str: str = "2026-08-31",
    seed: int = 42
):
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    transactions = []
    tx_counter = 1

    # 1. Define Subscriptions Metadata
    # Reference evaluation date is 2026-09-05
    subscriptions_meta = [
        {
            "merchant": "Spotify",
            "category": "Music Streaming",
            "day": 5,
            "amounts": [(start_date, end_date, 119.0)],
            "last_usage_date": "2026-09-03",
            "payment_method": "AutoPay",
        },
        {
            "merchant": "YouTube Premium",
            "category": "Streaming Video",
            "day": 10,
            "amounts": [(start_date, end_date, 149.0)],
            "last_usage_date": "2026-09-04",
            "payment_method": "AutoPay",
        },
        {
            "merchant": "Microsoft 365",
            "category": "Productivity",
            "day": 15,
            "amounts": [(start_date, end_date, 489.0)],
            "last_usage_date": "2026-09-02",
            "payment_method": "Card",
        },
        {
            "merchant": "Amazon Prime",
            "category": "Streaming Video",
            "day": 1,
            "amounts": [(start_date, end_date, 299.0)],
            "last_usage_date": "2026-09-04",
            "payment_method": "AutoPay",
        },
        {
            "merchant": "Substack Pro",
            "category": "Media",
            "day": 25,
            "amounts": [(start_date, end_date, 399.0)],
            "last_usage_date": "2026-09-03",
            "payment_method": "Card",
        },
        {
            "merchant": "VPN Shield",
            "category": "Security",
            "day": 28,
            "amounts": [(start_date, end_date, 299.0)],
            "last_usage_date": "2026-09-01",
            "payment_method": "Card",
        },
        # Price Increase: Netflix ₹649 -> ₹799
        {
            "merchant": "Netflix",
            "category": "Streaming Video",
            "day": 12,
            "amounts": [
                (start_date, date(2026, 5, 31), 649.0),
                (date(2026, 6, 1), end_date, 799.0),
            ],
            "last_usage_date": "2026-09-01",
            "payment_method": "AutoPay",
        },
        # Price Increase: NewsPlus ₹199 -> ₹249
        {
            "merchant": "NewsPlus",
            "category": "Media",
            "day": 18,
            "amounts": [
                (start_date, date(2026, 4, 30), 199.0),
                (date(2026, 5, 1), end_date, 249.0),
            ],
            "last_usage_date": "2026-08-31",
            "payment_method": "AutoPay",
        },
        # Unused: FitnessPro (91 days inactive relative to 2026-09-05)
        {
            "merchant": "FitnessPro",
            "category": "Fitness",
            "day": 20,
            "amounts": [(start_date, end_date, 499.0)],
            "last_usage_date": "2026-06-06",
            "payment_method": "AutoPay",
        },
        # Unused: GamingPlus (105 days inactive)
        {
            "merchant": "GamingPlus",
            "category": "Entertainment",
            "day": 22,
            "amounts": [(start_date, end_date, 699.0)],
            "last_usage_date": "2026-05-23",
            "payment_method": "Card",
        },
        # Upcoming Renewal: Adobe (₹2672, next renewal 2026-09-10 - 5 days away)
        {
            "merchant": "Adobe",
            "category": "Design",
            "day": 10,
            "amounts": [(start_date, end_date, 2672.0)],
            "last_usage_date": "2026-09-03",
            "payment_method": "Card",
        },
        # Overlap + Upcoming Renewal: Dropbox (₹800, Cloud Storage, next renewal 2026-09-08 - 3 days away)
        {
            "merchant": "Dropbox",
            "category": "Cloud Storage",
            "day": 8,
            "amounts": [(start_date, end_date, 800.0)],
            "last_usage_date": "2026-08-25",
            "payment_method": "Card",
        },
        # Overlap: Google One (₹149, Cloud Storage)
        {
            "merchant": "Google One",
            "category": "Cloud Storage",
            "day": 3,
            "amounts": [(start_date, end_date, 149.0)],
            "last_usage_date": "2026-09-04",
            "payment_method": "AutoPay",
        },
        # Overlap + Upcoming Renewal: CloudBox (₹799, Cloud Storage, next renewal 2026-09-17 - 12 days away)
        {
            "merchant": "CloudBox",
            "category": "Cloud Storage",
            "day": 17,
            "amounts": [(start_date, end_date, 799.0)],
            "last_usage_date": "2026-08-20",
            "payment_method": "AutoPay",
        },
    ]

    # Generate recurring subscription transactions for each month in date range
    curr_month = start_date.replace(day=1)
    while curr_month <= end_date:
        for sub in subscriptions_meta:
            tx_day = min(sub["day"], 28)
            tx_date = date(curr_month.year, curr_month.month, tx_day)
            if start_date <= tx_date <= end_date:
                # Find amount for tx_date
                amt = 0.0
                for s_date, e_date, val in sub["amounts"]:
                    if s_date <= tx_date <= e_date:
                        amt = val
                        break
                if amt > 0:
                    transactions.append({
                        "transaction_id": f"T{tx_counter:05d}",
                        "date": tx_date.strftime("%Y-%m-%d"),
                        "merchant": sub["merchant"],
                        "amount": amt,
                        "category": "Subscription",
                        "payment_method": sub["payment_method"],
                        "description": f"Monthly subscription fee - {sub['merchant']}",
                    })
                    tx_counter += 1
        curr_month += relativedelta(months=1)

    # 2. Generate Everyday Non-Subscription Transactions (~850 records)
    non_sub_merchants = [
        {"name": "Supermarket Fresh", "category": "Groceries", "min": 350.0, "max": 3500.0, "methods": ["Card", "UPI"]},
        {"name": "StarCoffee Cafe", "category": "Dining", "min": 180.0, "max": 480.0, "methods": ["UPI"]},
        {"name": "Uber Rides", "category": "Transport", "min": 150.0, "max": 650.0, "methods": ["Card", "UPI"]},
        {"name": "Shell Fuel Station", "category": "Transport", "min": 1200.0, "max": 3200.0, "methods": ["Card"]},
        {"name": "Local Diner", "category": "Dining", "min": 250.0, "max": 1400.0, "methods": ["UPI"]},
        {"name": "TechStore Electronics", "category": "Shopping", "min": 500.0, "max": 12000.0, "methods": ["Card", "NetBanking"]},
        {"name": "City Electricity Board", "category": "Utilities", "min": 1500.0, "max": 4200.0, "methods": ["AutoPay", "UPI"]},
        {"name": "Water Works Dept", "category": "Utilities", "min": 300.0, "max": 850.0, "methods": ["AutoPay"]},
        {"name": "Zomato Food Delivery", "category": "Dining", "min": 220.0, "max": 950.0, "methods": ["UPI"]},
        {"name": "Swiggy Instamart", "category": "Groceries", "min": 180.0, "max": 1900.0, "methods": ["UPI"]},
        {"name": "PharmaCare Chemist", "category": "Shopping", "min": 120.0, "max": 1600.0, "methods": ["Card", "UPI"]},
        {"name": "BookMyShow", "category": "Entertainment", "min": 300.0, "max": 1400.0, "methods": ["UPI"]},
    ]

    total_days = (end_date - start_date).days + 1
    # Aim for ~840 non-sub transactions (approx 2.3 tx per day)
    for day_offset in range(total_days):
        current_day = start_date + timedelta(days=day_offset)
        # 1 to 4 transactions per day
        num_tx = random.randint(1, 4)
        for _ in range(num_tx):
            m_info = random.choice(non_sub_merchants)
            amt = round(random.uniform(m_info["min"], m_info["max"]), 2)
            method = random.choice(m_info["methods"])
            transactions.append({
                "transaction_id": f"T{tx_counter:05d}",
                "date": current_day.strftime("%Y-%m-%d"),
                "merchant": m_info["name"],
                "amount": amt,
                "category": m_info["category"],
                "payment_method": method,
                "description": f"{m_info['category']} purchase at {m_info['name']}",
            })
            tx_counter += 1

    # Sort transactions chronologically
    transactions.sort(key=lambda x: x["date"])

    # Re-assign IDs sequentially
    for idx, tx in enumerate(transactions, start=1):
        tx["transaction_id"] = f"T{idx:05d}"

    # Save transactions.csv
    tx_file_path = os.path.join(output_dir, "transactions.csv")
    fieldnames = ["transaction_id", "date", "merchant", "amount", "category", "payment_method", "description"]
    with open(tx_file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)

    # Save subscriptions.csv metadata / usage telemetry
    sub_file_path = os.path.join(output_dir, "subscriptions.csv")
    sub_fieldnames = ["subscription_id", "merchant", "category", "frequency", "last_usage_date"]
    sub_rows = []
    for idx, sub in enumerate(subscriptions_meta, start=1):
        sub_rows.append({
            "subscription_id": f"SUB-{idx:03d}",
            "merchant": sub["merchant"],
            "category": sub["category"],
            "frequency": "monthly",
            "last_usage_date": sub["last_usage_date"],
        })
    with open(sub_file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sub_fieldnames)
        writer.writeheader()
        writer.writerows(sub_rows)

    print(f"Generated {len(transactions)} transaction records in '{tx_file_path}'.")
    print(f"Generated {len(sub_rows)} subscription telemetry records in '{sub_file_path}'.")
    return len(transactions), len(sub_rows)


if __name__ == "__main__":
    generate_dataset()
