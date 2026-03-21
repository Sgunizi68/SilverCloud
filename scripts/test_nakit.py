import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.database import SessionLocal
from app.modules.invoicing import queries
from datetime import date

app = create_app()

def run_tests():
    with app.app_context():
        db = SessionLocal()
        print("--- Nakit CRUD Testi Başlıyor ---")
        
        # 1. Create
        data = {
            'Tarih': date(2026, 3, 1),
            'Tutar': 1250.50,
            'Tip': 'Bankaya Yatan',
            'Donem': 2603,
            'Sube_ID': 1  # Varsayılan test şubesi
        }
        yeni_kayit = queries.create_nakit(db, data)
        print(f"[OK] Kayıt eklendi: ID={yeni_kayit.Nakit_ID}")
        kayit_id = yeni_kayit.Nakit_ID
        
        # 2. Read Single & List
        c_kayit = queries.get_nakit_by_id(db, kayit_id)
        if c_kayit and float(c_kayit.Tutar) == 1250.50:
            print("[OK] Kayıt başarıyla okundu.")
        else:
            print("[HATA] Kayıt okuma başarısız.")
            
        liste = queries.get_nakitler(db, sube_id=1, donem=2603)
        if len(liste) > 0 and any(k.Nakit_ID == kayit_id for k in liste):
            print("[OK] Liste sorgusu başarılı.")
        else:
            print("[HATA] Liste sorgusu başarısız.")
            
        # 3. Update
        update_data = {'Tutar': 3000.00, 'Tip': 'Şube Kasasına Yatan'}
        u_kayit = queries.update_nakit(db, kayit_id, update_data)
        if u_kayit and float(u_kayit.Tutar) == 3000.00:
            print("[OK] Kayıt güncellendi (Tutar 3000 oldu).")
        else:
            print("[HATA] Güncelleme başarısız.")
            
        # 4. Delete
        silindi_mi = queries.delete_nakit(db, kayit_id)
        if silindi_mi:
            e_kayit = queries.get_nakit_by_id(db, kayit_id)
            if not e_kayit:
                print("[OK] Kayıt başarıyla silindi.")
            else:
                print("[HATA] Silindi denen kayıt hala mevcut.")
        else:
            print("[HATA] Silme işlemi False döndürdü.")
            
        print("--- Test Tamamlandı ---")
        db.close()

if __name__ == "__main__":
    run_tests()
