from app import create_app
from app.modules.reports.queries import dashboard_report
from datetime import date

app = create_app('development')
with app.app_context():
    res = dashboard_report(sube_id=1, donem=2511)
    
    print("--- FULL GIDER LIST ---")
    for cat in res['giderler']:
        print(f"\n[{cat['label']}] TOTAL: {cat['amount']:,.2f}")
        for child in cat['children']:
            print(f"  - {child['label']}: {child['amount']:,.2f}")
