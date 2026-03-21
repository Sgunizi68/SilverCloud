from app import create_app
from app.modules.invoicing.queries import create_efatura_bulk
from app.common.database import get_db_session
from app.models.models import EFatura, EFaturaReferans
from sqlalchemy import select, delete

app = create_app()
with app.app_context():
    db = get_db_session()
    try:
        # 1. Clean up any existing test data if needed (optional)
        # 2. Mock some data
        # We need a reference for a specific Alici_Unvani
        test_unvan = "TEST_ALICI_UNVANI"
        existing_ref = db.execute(select(EFaturaReferans).where(EFaturaReferans.Alici_Unvani == test_unvan)).scalar_one_or_none()
        if not existing_ref:
            new_ref = EFaturaReferans(Alici_Unvani=test_unvan, Kategori_ID=1, Referans_Kodu="TEST_REF")
            db.add(new_ref)
            db.commit()
            print(f"Created test reference for {test_unvan}")
        
        test_data = [
            {
                "Sube_ID": 1,
                "Fatura_No": "TEST-GELEN-001",
                "Alici_Unvani": test_unvan,
                "Fatura_Tutari": 100.0,
                "Fatura_Tarihi": "2026-02-23",
                "Donem": 2602,
                "Giden_Fatura": False  # Should get Kategori_ID=1
            },
            {
                "Sube_ID": 1,
                "Fatura_No": "TEST-GIDEN-001",
                "Alici_Unvani": test_unvan,
                "Fatura_Tutari": 200.0,
                "Fatura_Tarihi": "2026-02-23",
                "Donem": 2602,
                "Giden_Fatura": True  # Should get Kategori_ID=None
            }
        ]
        
        # Remove existing if any
        db.execute(delete(EFatura).where(EFatura.Fatura_Numarasi.in_(["TEST-GELEN-001", "TEST-GIDEN-001"])))
        db.commit()
        
        result = create_efatura_bulk(db, test_data)
        print(f"Bulk Create Result: {result}")
        
        # Verify
        inv_gelen = db.execute(select(EFatura).where(EFatura.Fatura_Numarasi == "TEST-GELEN-001")).scalar_one()
        inv_giden = db.execute(select(EFatura).where(EFatura.Fatura_Numarasi == "TEST-GIDEN-001")).scalar_one()
        
        print(f"Gelen Invoice Kategori_ID: {inv_gelen.Kategori_ID} (Expected: 1)")
        print(f"Giden Invoice Kategori_ID: {inv_giden.Kategori_ID} (Expected: None)")
        print(f"Gelen Invoice Aciklama: {inv_gelen.Aciklama} (Expected: None)")
        
        if inv_gelen.Kategori_ID == 1 and inv_giden.Kategori_ID is None and inv_gelen.Aciklama is None:
            print("VERIFICATION_SUCCESS")
        else:
            print("VERIFICATION_FAILURE")
            
    finally:
        db.close()
