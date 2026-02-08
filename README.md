# SilverCloud - Migrasyon ve Dönüşüm Planı

Bu proje, `gumusbulut` klasörü altındaki 3 katmanlı (Controller-Service-Repository) yapının, `Gemini.md` spesifikasyonlarına uygun olarak 2 katmanlı (Route-Model) Flask mimarisine dönüştürülmesini hedefler.

## Mimari Hedef

*   **Eski:** Controller -> Service -> Repository -> DB
*   **Yeni:** Flask Route -> SQLAlchemy Model -> DB

## Dönüşüm Görevleri (Tasks)

### 1. Çevre ve Konfigürasyon Hazırlığı
- [ ] **Bağımlılıkların Kurulumu:** `Flask`, `Flask-SQLAlchemy`, `python-dotenv` paketlerini içeren `requirements.txt` oluştur.
- [ ] **.env Yapılandırması:** Veritabanı bağlantı bilgilerini (connection string) ve `SECRET_KEY` değerini tutacak `.env` dosyasını oluştur.
- [ ] **Git Ayarı:** `.env` dosyasının `.gitignore` içinde olduğundan emin ol.

### 2. Veritabanı Katmanı (Model)
- [ ] **ORM Kurulumu:** `app.py` veya `extensions.py` içinde `SQLAlchemy` nesnesini başlat ve `.env` üzerinden `SQLALCHEMY_DATABASE_URI` ayarını yap.
- [ ] **Model Migrasyonu:** `gumusbulut` içindeki entity sınıflarını analiz et ve bunları `models.py` içinde `db.Model`'den türeyen SQLAlchemy sınıflarına çevir.

### 3. İş Mantığı ve Route Dönüşümü (Core)
- [ ] **Route İskeleti:** `gumusbulut` içindeki her Controller için Flask içinde bir `Blueprint` veya route fonksiyonu tanımla.
- [ ] **Service Katmanını Eritme:** Service sınıflarındaki iş mantığını (validasyonlar, hesaplamalar) doğrudan ilgili Flask route fonksiyonunun içine taşı.
- [ ] **Repository Katmanını Kaldırma:** Veritabanı sorgularını (SELECT, INSERT, UPDATE) Repository yerine doğrudan route içinde `Model.query` veya `db.session` kullanarak yaz.

### 4. Temizlik ve Test
- [ ] **Eski Kodun Silinmesi:** Dönüşüm tamamlandıktan sonra `gumusbulut` klasörünü veya eski katman dosyalarını arşivle/sil.
- [ ] **Endpoint Testleri:** Oluşturulan API uç noktalarının test edilmesi.

## Kurulum

```bash
pip install -r requirements.txt
flask run
```