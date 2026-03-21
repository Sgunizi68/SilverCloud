import os
import sys

base_path = r'C:\projects\SilverCloud'
sys.path.append(base_path)

from app import create_app
from app.common.database import get_db_session
from app.modules.invoicing import queries
from app.models import Odeme

app = create_app()

with app.app_context():
    db = get_db_session()
    
    print("--- TESTING GET ODEMELER ---")
    odemeler = queries.get_odemeler(db, limit=5)
    for o in odemeler:
        print(f"ID: {o.Odeme_ID}, Tip: {o.Tip}, Tutar: {o.Tutar}, Kategori_ID: {o.Kategori_ID}, Donem: {o.Donem}")
        
    print("\n--- TESTING UPDATE ODEME ---")
    if odemeler:
        test_id = odemeler[0].Odeme_ID
        print(f"Updating Odeme_ID: {test_id}")
        
        # Test updating Kategori
        updated = queries.update_odeme(db, test_id, kategori_id=1, donem=2503)
        print(f"After Update - Kategori_ID: {updated.Kategori_ID}, Donem: {updated.Donem}")
        
        # Revert changes to not mess with production data
        original_kat = odemeler[0].Kategori_ID
        original_donem = odemeler[0].Donem
        queries.update_odeme(
            db, 
            test_id, 
            kategori_id=original_kat, 
            donem=original_donem,
            kategori_clear=(original_kat is None),
            donem_clear=(original_donem is None)
        )
        print("Changes reverted successfully.")
    
    db.close()
