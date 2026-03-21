
import os, sys, codecs
from run import app
from app.common.database import get_db_session

target_firms = {
    'FASDAT GIDA DAĞITIM SANAYİ VE TİCARET ANONİM ŞİRKETİ': (48027.36, 55536.21, 148002.6, 155511.4),
    'G2MEKSPER SATIŞ VE DAĞITIM HİZMETLERİ ANONİM ŞİRKETİ': (4535.55, 28596.53, 97332.49, 121393.5),
    'Seher Gıda Pazarlama Sanayi Ve Ticaret Anonim Şirketi': (0, 7721.25, 27293.04, 35014.29),
    'COCA COLA SATIŞ VE DAĞITIM A.Ş.': (1605.52, 1788.06, 18654.52, 18837.06),
    'Pepsi Cola Servis ve Dağıtım Ltd. Şti.': (9154.08, 28453.07, 119887.5, 139186.5),
    'VOLKAN ŞERBETÇİ': (2059.9, 1747.44, 86136.43, 85823.97)
}

with app.app_context(), open('diff_output.txt', 'w', encoding='utf-8') as f:
    db = get_db_session()
    try:
        from app.modules.reports.queries import get_cari_borc_takip_raporu
        r = get_cari_borc_takip_raporu('2026-03-01', 1)
        
        firm_dict = {fi['name']: fi for fi in r['lists']['tumu']}
        
        for name, expected in target_firms.items():
            f.write(f"--- {name} ---\n")
            f_data = firm_dict.get(name)
            if not f_data:
                f.write("  NOT FOUND in report!\n")
                continue
                
            e_bak, e_mut, e_fat, e_ode = expected
            
            f.write(f"  Mutabakat: {f_data['mutabakat_tutar']:.2f} (Expected: {e_mut:.2f})\n")
            f.write(f"  Fatura:    {f_data['fatura_toplam']:.2f} (Expected: {e_fat:.2f})\n")
            f.write(f"  Odeme:     {f_data['odeme_toplam']:.2f} (Expected: {e_ode:.2f})\n")
            f.write(f"  Bakiye:    {f_data['balance']:.2f} (Expected: {e_bak:.2f})\n")
            
    finally:
        db.close()
