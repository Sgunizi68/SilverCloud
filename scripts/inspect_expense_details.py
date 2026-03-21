from app import create_app
from app.modules.reports.queries import dashboard_report
from datetime import date

app = create_app('development')
with app.app_context():
    res = dashboard_report(sube_id=1, donem=2511)
    
    for cat in res['giderler']:
        if cat['label'] in ["Satıştan İndirimler & Komisyonlar", "TD Ciro/Reklam Primi & Lojistik"]:
            print(f"\nCATEGORY: {cat['label']} (Total: {cat['amount']:,.2f})")
            for child in cat['children']:
                print(f"  - {child['label']}: {child['amount']:,.2f}")
