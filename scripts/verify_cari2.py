
from run import app
with app.app_context():
    from app.modules.reports.queries import get_cari_borc_takip_raporu
    r = get_cari_borc_takip_raporu('2026-03-01', 1)
    print('=== SUMMARY ===')
    print('Summary:', r['summary'])
    print()
    print('=== CARI BORCLAR ===')
    for firm in r['lists']['cari_borclar']:
        name = firm['name']
        bal = firm['balance']
        mut = firm['mutabakat_tutar']
        fat = firm['fatura_toplam']
        ode = firm['odeme_toplam']
        n_fatura = len(firm['fatura_details'])
        n_odeme  = len(firm['odeme_details'])
        print(f"  {name}")
        print(f"    Mutabakat: {mut:.2f}, Fatura: {fat:.2f} ({n_fatura} rows), Odeme: {ode:.2f} ({n_odeme} rows), Bakiye: {bal:.2f}")
        if firm['fatura_details']:
            first = firm['fatura_details'][0]
            print(f"    First fatura: {first['no']} {first['date']} {first['amount']:.2f}")
        if firm['odeme_details']:
            first = firm['odeme_details'][0]
            print(f"    First odeme: {first['date']} {first['amount']:.2f}")
        print()
