from app import create_app
from app.modules.reports.queries import dashboard_report
from datetime import date
import json

app = create_app('development')
with app.app_context():
    # Period 2511, Sube 1 (Brandium)
    # The queries.py uses donem if provided, else calculates from start_date/end_date
    res = dashboard_report(sube_id=1, donem=2511)
    
    print(f"--- VERIFICATION FOR PERIOD 2511 ---")
    print(f"Total Revenue: {res['financial_summary']['total_revenue']:,.2f}")
    print(f"Total Expense: {res['financial_summary']['total_expense']:,.2f}")
    
    print("\nEXPENSE CATEGORIES:")
    for cat in res['giderler']:
        print(f"  {cat['label']}: {cat['amount']:,.2f}")
        for child in cat['children']:
            if len(cat['children']) > 1 or child['label'] != cat['label']:
                print(f"    - {child['label']}: {child['amount']:,.2f}")

    target_expense = 2206690.18
    actual_expense = res['financial_summary']['total_expense']
    
    if abs(actual_expense - target_expense) < 0.01:
        print(f"\nSUCCESS: Expense total matches the target {target_expense:,.2f}!")
    else:
        print(f"\nFAILURE: Expense total {actual_expense:,.2f} does NOT match the target {target_expense:,.2f}!")
        print(f"Difference: {actual_expense - target_expense:,.2f}")
