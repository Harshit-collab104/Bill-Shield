"""
BillShield Financial Analysis Runner Script
"""

import sys
import io
from datetime import date
from backend.services.detection import analyze_finances

# Ensure UTF-8 output for Windows console terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    tx_path = "backend/data/transactions.csv"
    sub_path = "backend/data/subscriptions.csv"
    
    # Reference evaluation date matching hackathon dataset state
    reference_date = date(2026, 9, 5)

    report = analyze_finances(
        transactions_source=tx_path,
        subscriptions_csv_path=sub_path,
        reference_date=reference_date,
        unused_threshold_days=90,
        renewal_window_days=5,
    )

    print("==================================================")
    print("BILLSHIELD FINANCIAL ANALYSIS")
    print("=============================")
    print()
    print(f"Transactions analyzed: {report.transactions_analyzed}")
    print()
    print(f"Subscriptions detected: {report.subscriptions_detected}")
    print()
    print(f"Monthly recurring spend: ₹{report.monthly_recurring_spend:,.0f}")
    print()
    print(f"Potential monthly savings: ₹{report.potential_monthly_savings:,.0f}")
    print()
    print(f"Potential annual savings: ₹{report.potential_annual_savings:,.0f}")
    print()
    print(f"Price increases detected: {len(report.price_increases)}")
    print()
    print(f"Potentially unused subscriptions: {len(report.potentially_unused)}")
    print()
    print(f"Upcoming renewals: {len(report.upcoming_renewals)}")
    print()
    print(f"Potential overlaps: {len(report.potential_overlaps)}")
    print()
    print("==================================================")


if __name__ == "__main__":
    main()
