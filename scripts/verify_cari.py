
from run import app
with app.app_context():
    from app.modules.reports.queries import get_cari_borc_takip_raporu
    r = get_cari_borc_takip_raporu('2026-03-01', 1)
    print('Summary:', r['summary'])
    cari = r['lists']['cari_borclar']
    for firm in cari[:5]:
        name = firm['name']
        balance = firm['balance']
        print(f"  {name}: {balance:.2f}  (mutabakat={firm['mutabakat_tutar']:.2f}, fatura={firm['fatura_toplam']:.2f}, odeme={firm['odeme_toplam']:.2f})")
