from app import create_app
from app.models.models import Kategori

app = create_app()
with app.app_context():
    ks = Kategori.query.all()
    print("CATEGORIES_START")
    for k in ks:
        print(f"ID:{k.Kategori_ID}|Name:{k.Kategori_Adi}|Tip:{k.Tip}")
    print("CATEGORIES_END")
