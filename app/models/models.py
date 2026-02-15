"""
SQLAlchemy ORM Models
Organized by business domain.
All models cleaned up from GumusBulut and optimized for SQLAlchemy 2.0.
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean, 
    DECIMAL, Enum, ForeignKey, LargeBinary, event
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.common.database import db


# ============================================================================
# REFERENCE MODELS (Foundation entities)
# ============================================================================

class Sube(db.Model):
    """Branch/Location entity"""
    __tablename__ = "Sube"
    __table_args__ = {"extend_existing": True}

    Sube_ID = Column(Integer, primary_key=True, index=True)
    Sube_Adi = Column(String(100), nullable=False, index=True)
    Aciklama = Column(Text, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    calisanlar = relationship("Calisan", back_populates="sube")
    kullanici_rolleri = relationship("KullaniciRol", back_populates="sube")
    e_faturalar = relationship("EFatura", back_populates="sube")
    b2b_ekstreler = relationship("B2BEkstre", back_populates="sube")
    diger_harcamalar = relationship("DigerHarcama", back_populates="sube")
    gelirler = relationship("Gelir", back_populates="sube")
    gelir_ekstralar = relationship("GelirEkstra", back_populates="sube")
    stok_sayimlar = relationship("StokSayim", back_populates="sube")
    stok_fiyatlar = relationship("StokFiyat", back_populates="sube")
    puantajlar = relationship("Puantaj", back_populates="sube")
    avans_istekler = relationship("AvansIstek", back_populates="sube")
    nakitler = relationship("Nakit", back_populates="sube")
    odemeler = relationship("Odeme", back_populates="sube")
    pos_hareketleri = relationship("POSHareketleri", back_populates="sube")
    calisan_talepler = relationship("CalisanTalep", back_populates="sube")
    yemek_cekiler = relationship("YemekCeki", back_populates="sube")

    def __repr__(self):
        return f"<Sube {self.Sube_Adi}>"


class Kullanici(db.Model):
    """User entity"""
    __tablename__ = "Kullanici"
    __table_args__ = {"extend_existing": True}

    Kullanici_ID = Column(Integer, primary_key=True, index=True)
    Adi_Soyadi = Column(String(100), nullable=False)
    Kullanici_Adi = Column(String(50), nullable=False, unique=True, index=True)
    Password = Column(String(255), nullable=False)  # Hashed password
    Email = Column(String(100), nullable=True, index=True)
    Expire_Date = Column(Date, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    kullanici_rolleri = relationship("KullaniciRol", back_populates="kullanici")
    is_onay_veren_talepler = relationship(
        "CalisanTalep",
        foreign_keys="[CalisanTalep.Is_Onay_Veren_Kullanici_ID]",
        back_populates="is_onay_veren_kullanici"
    )
    ssk_onay_veren_talepler = relationship(
        "CalisanTalep",
        foreign_keys="[CalisanTalep.SSK_Onay_Veren_Kullanici_ID]",
        back_populates="ssk_onay_veren_kullanici"
    )

    def __repr__(self):
        return f"<Kullanici {self.Kullanici_Adi}>"


class Rol(db.Model):
    """Role entity"""
    __tablename__ = "Rol"
    __table_args__ = {"extend_existing": True}

    Rol_ID = Column(Integer, primary_key=True, index=True)
    Rol_Adi = Column(String(50), nullable=False, unique=True, index=True)
    Aciklama = Column(Text, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    kullanici_rolleri = relationship("KullaniciRol", back_populates="rol")
    rol_yetkileri = relationship("RolYetki", back_populates="rol")

    def __repr__(self):
        return f"<Rol {self.Rol_Adi}>"


class Yetki(db.Model):
    """Permission entity"""
    __tablename__ = "Yetki"
    __table_args__ = {"extend_existing": True}

    Yetki_ID = Column(Integer, primary_key=True, index=True)
    Yetki_Adi = Column(String(100), nullable=False, unique=True, index=True)
    Aciklama = Column(Text, nullable=True)
    Tip = Column(String(50), nullable=True)  # e.g., 'Ekran', 'Islem'
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    rol_yetkileri = relationship("RolYetki", back_populates="yetki")

    def __repr__(self):
        return f"<Yetki {self.Yetki_Adi}>"


class KullaniciRol(db.Model):
    """User-Role assignment (pivot table)"""
    __tablename__ = "Kullanici_Rol"
    __table_args__ = {"extend_existing": True}

    Kullanici_ID = Column(Integer, ForeignKey("Kullanici.Kullanici_ID"), primary_key=True, index=True)
    Rol_ID = Column(Integer, ForeignKey("Rol.Rol_ID"), primary_key=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), primary_key=True, index=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    kullanici = relationship("Kullanici", back_populates="kullanici_rolleri")
    rol = relationship("Rol", back_populates="kullanici_rolleri")
    sube = relationship("Sube", back_populates="kullanici_rolleri")

    def __repr__(self):
        return f"<KullaniciRol K:{self.Kullanici_ID} R:{self.Rol_ID}>"


class RolYetki(db.Model):
    """Role-Permission assignment (pivot table)"""
    __tablename__ = "Rol_Yetki"
    __table_args__ = {"extend_existing": True}

    Rol_ID = Column(Integer, ForeignKey("Rol.Rol_ID"), primary_key=True, index=True)
    Yetki_ID = Column(Integer, ForeignKey("Yetki.Yetki_ID"), primary_key=True, index=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    rol = relationship("Rol", back_populates="rol_yetkileri")
    yetki = relationship("Yetki", back_populates="rol_yetkileri")

    def __repr__(self):
        return f"<RolYetki R:{self.Rol_ID} Y:{self.Yetki_ID}>"


class Deger(db.Model):
    """Configurable values (exchange rates, coefficients, etc.)"""
    __tablename__ = "Deger"
    __table_args__ = {"extend_existing": True}

    Deger_ID = Column(Integer, primary_key=True, index=True)
    Deger_Adi = Column(String(100), nullable=False, index=True)
    Gecerli_Baslangic_Tarih = Column(Date, nullable=False)
    Gecerli_Bitis_Tarih = Column(Date, nullable=False, default="2100-01-01")
    Deger_Aciklama = Column(Text, nullable=True)
    Deger = Column(DECIMAL(15, 2), nullable=False)

    def __repr__(self):
        return f"<Deger {self.Deger_Adi}>"


class UstKategori(db.Model):
    """Parent category"""
    __tablename__ = "UstKategori"
    __table_args__ = {"extend_existing": True}

    UstKategori_ID = Column(Integer, primary_key=True, index=True)
    UstKategori_Adi = Column(String(100), nullable=False, unique=True, index=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    kategoriler = relationship("Kategori", back_populates="ust_kategori")

    def __repr__(self):
        return f"<UstKategori {self.UstKategori_Adi}>"


class Kategori(db.Model):
    """Category"""
    __tablename__ = "Kategori"
    __table_args__ = {"extend_existing": True}

    Kategori_ID = Column(Integer, primary_key=True, index=True)
    Kategori_Adi = Column(String(100), nullable=False, index=True)
    Ust_Kategori_ID = Column(Integer, ForeignKey("UstKategori.UstKategori_ID"), nullable=True, index=True)
    Tip = Column(
        Enum('Gelir', 'Gider', 'Bilgi', 'Ödeme', 'Giden Fatura'),
        nullable=False,
        index=True
    )
    Aktif_Pasif = Column(Boolean, default=True, index=True)
    Gizli = Column(Boolean, default=False)

    # Relationships
    ust_kategori = relationship("UstKategori", back_populates="kategoriler")
    e_faturalar = relationship("EFatura", back_populates="kategori")
    b2b_ekstreler = relationship("B2BEkstre", back_populates="kategori")
    diger_harcamalar = relationship("DigerHarcama", back_populates="kategori")
    gelirler = relationship("Gelir", back_populates="kategori")
    odemeler = relationship("Odeme", back_populates="kategori")
    odeme_referanslar = relationship("OdemeReferans", back_populates="kategori")

    def __repr__(self):
        return f"<Kategori {self.Kategori_Adi}>"


# ============================================================================
# INVOICING MODELS
# ============================================================================

class EFatura(db.Model):
    """Electronic invoice"""
    __tablename__ = "e_Fatura"
    __table_args__ = {"extend_existing": True}

    Fatura_ID = Column(Integer, primary_key=True, index=True)
    Fatura_Tarihi = Column(Date, nullable=False, index=True)
    Fatura_Numarasi = Column(String(50), nullable=False, unique=True, index=True)
    Alici_Unvani = Column(String(200), nullable=False, index=True)
    Alici_VKN_TCKN = Column(String(20), nullable=True)
    Tutar = Column(DECIMAL(15, 2), nullable=False)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=True, index=True)
    Aciklama = Column(Text, nullable=True)
    Donem = Column(Integer, nullable=False, index=True)  # YYMM format
    Ozel = Column(Boolean, default=False)
    Gunluk_Harcama = Column(Boolean, default=False)
    Giden_Fatura = Column(Boolean, default=False)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori", back_populates="e_faturalar")
    sube = relationship("Sube", back_populates="e_faturalar")

    def __repr__(self):
        return f"<EFatura {self.Fatura_Numarasi}>"


class B2BEkstre(db.Model):
    """B2B statement/extract"""
    __tablename__ = "B2B_Ekstre"
    __table_args__ = {"extend_existing": True}

    Ekstre_ID = Column(Integer, primary_key=True, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    Fis_No = Column(String(50), nullable=False, index=True)
    Fis_Turu = Column(String(50), nullable=True)
    Aciklama = Column(Text, nullable=True)
    Borc = Column(DECIMAL(15, 2), default=0.00)
    Alacak = Column(DECIMAL(15, 2), default=0.00)
    Toplam_Bakiye = Column(DECIMAL(15, 2), nullable=True)
    Fatura_No = Column(String(50), nullable=True, index=True)
    Fatura_Metni = Column(Text, nullable=True)
    Donem = Column(Integer, nullable=False, index=True)  # YYMM format
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori", back_populates="b2b_ekstreler")
    sube = relationship("Sube", back_populates="b2b_ekstreler")

    def __repr__(self):
        return f"<B2BEkstre {self.Fis_No}>"


class DigerHarcama(db.Model):
    """Other expenses"""
    __tablename__ = "Diger_Harcama"
    __table_args__ = {"extend_existing": True}

    Harcama_ID = Column(Integer, primary_key=True, index=True)
    Alici_Adi = Column(String(200), nullable=False)
    Belge_Numarasi = Column(String(50), nullable=True)
    Belge_Tarihi = Column(Date, nullable=False, index=True)
    Donem = Column(Integer, nullable=False, index=True)  # YYMM format
    Tutar = Column(DECIMAL(15, 2), nullable=False)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=False, index=True)
    Harcama_Tipi = Column(
        Enum('Nakit', 'Banka Ödeme', 'Kredi Kartı'),
        nullable=False
    )
    Gunluk_Harcama = Column(Boolean, default=False)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Aciklama = Column(String(45), nullable=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())
    Imaj = Column(LargeBinary, nullable=True)
    Imaj_Adi = Column(String(255), nullable=True)

    # Relationships
    kategori = relationship("Kategori", back_populates="diger_harcamalar")
    sube = relationship("Sube", back_populates="diger_harcamalar")

    def __repr__(self):
        return f"<DigerHarcama {self.Harcama_ID}>"


class Odeme(db.Model):
    """Payment"""
    __tablename__ = "Odeme"
    __table_args__ = {"extend_existing": True}

    Odeme_ID = Column(Integer, primary_key=True, index=True)
    Tip = Column(String(50), nullable=False, index=True)
    Hesap_Adi = Column(String(50), nullable=False)
    Tarih = Column(Date, nullable=False, index=True)
    Aciklama = Column(String(200), nullable=False)
    Tutar = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=True, index=True)
    Donem = Column(Integer, nullable=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), default=1, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori", back_populates="odemeler")
    sube = relationship("Sube", back_populates="odemeler")

    def __repr__(self):
        return f"<Odeme {self.Odeme_ID}>"


class OdemeReferans(db.Model):
    """Payment reference"""
    __tablename__ = "Odeme_Referans"
    __table_args__ = {"extend_existing": True}

    Referans_ID = Column(Integer, primary_key=True, index=True)
    Referans_Metin = Column(String(50), nullable=False, unique=True, index=True)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=False, index=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori", back_populates="odeme_referanslar")

    def __repr__(self):
        return f"<OdemeReferans {self.Referans_Metin}>"


class Nakit(db.Model):
    """Cash/Cash register"""
    __tablename__ = "Nakit"
    __table_args__ = {"extend_existing": True}

    Nakit_ID = Column(Integer, primary_key=True, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    Kayit_Tarih = Column(DateTime, server_default=func.now())
    Tutar = Column(DECIMAL(15, 2), nullable=False)
    Tip = Column(String(50), default='Bankaya Yatan')
    Donem = Column(Integer, nullable=False, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Imaj_Adı = Column(String(255), nullable=True)
    Imaj = Column(LargeBinary, nullable=True)

    # Relationships
    sube = relationship("Sube", back_populates="nakitler")

    def __repr__(self):
        return f"<Nakit {self.Nakit_ID}>"


class EFaturaReferans(db.Model):
    """E-Invoice reference/mapping"""
    __tablename__ = "e_Fatura_Referans"
    __table_args__ = {"extend_existing": True}

    Alici_Unvani = Column(String(200), primary_key=True, index=True)
    Referans_Kodu = Column(String(50), nullable=False)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=True, index=True)
    Aciklama = Column(Text, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori")

    def __repr__(self):
        return f"<EFaturaReferans {self.Alici_Unvani}>"


class POSHareketleri(db.Model):
    """POS transactions"""
    __tablename__ = "POS_Hareketleri"
    __table_args__ = {"extend_existing": True}

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Islem_Tarihi = Column(Date, nullable=False, index=True)
    Hesaba_Gecis = Column(Date, nullable=False, index=True)
    Para_Birimi = Column(String(5), nullable=False)
    Islem_Tutari = Column(DECIMAL(15, 2), nullable=False)
    Kesinti_Tutari = Column(DECIMAL(15, 2), default=0.00)
    Net_Tutar = Column(DECIMAL(15, 2), nullable=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=True, index=True)

    # Relationships
    sube = relationship("Sube", back_populates="pos_hareketleri")

    def __repr__(self):
        return f"<POSHareketleri {self.ID}>"


class Gelir(db.Model):
    """Revenue/Income"""
    __tablename__ = "Gelir"
    __table_args__ = {"extend_existing": True}

    Gelir_ID = Column(Integer, primary_key=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=False, index=True)
    Tutar = Column(DECIMAL(15, 2), nullable=False)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    sube = relationship("Sube", back_populates="gelirler")
    kategori = relationship("Kategori", back_populates="gelirler")

    def __repr__(self):
        return f"<Gelir {self.Gelir_ID}>"


class GelirEkstra(db.Model):
    """Revenue extra data"""
    __tablename__ = "GelirEkstra"
    __table_args__ = {"extend_existing": True}

    GelirEkstra_ID = Column(Integer, primary_key=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    RobotPos_Tutar = Column(DECIMAL(15, 2), nullable=False)
    ZRapor_Tutar = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    Tabak_Sayisi = Column(Integer, nullable=False, default=0)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    sube = relationship("Sube", back_populates="gelir_ekstralar")

    def __repr__(self):
        return f"<GelirEkstra {self.GelirEkstra_ID}>"


# ============================================================================
# INVENTORY MODELS
# ============================================================================

class Stok(db.Model):
    """Stock/Inventory item"""
    __tablename__ = "Stok"
    __table_args__ = {"extend_existing": True}

    Stok_ID = Column(Integer, primary_key=True, index=True)
    Urun_Grubu = Column(String(100), nullable=False, index=True)
    Malzeme_Kodu = Column(String(50), nullable=False, unique=True, index=True)
    Malzeme_Aciklamasi = Column(Text, nullable=False)
    Birimi = Column(String(20), nullable=False)
    Sinif = Column(String(50), nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    stok_fiyatlar = relationship("StokFiyat", back_populates="stok")
    stok_sayimlar = relationship("StokSayim", back_populates="stok")

    def __repr__(self):
        return f"<Stok {self.Malzeme_Kodu}>"


class StokFiyat(db.Model):
    """Stock price"""
    __tablename__ = "Stok_Fiyat"
    __table_args__ = {"extend_existing": True}

    Fiyat_ID = Column(Integer, primary_key=True, index=True)
    Malzeme_Kodu = Column(String(50), ForeignKey("Stok.Malzeme_Kodu"), nullable=False, index=True)
    Gecerlilik_Baslangic_Tarih = Column(Date, nullable=False, index=True)
    Fiyat = Column(DECIMAL(10, 2), nullable=False)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    stok = relationship("Stok", back_populates="stok_fiyatlar")
    sube = relationship("Sube", back_populates="stok_fiyatlar")

    def __repr__(self):
        return f"<StokFiyat {self.Fiyat_ID}>"


class StokSayim(db.Model):
    """Stock count/inventory"""
    __tablename__ = "Stok_Sayim"
    __table_args__ = {"extend_existing": True}

    Sayim_ID = Column(Integer, primary_key=True, index=True)
    Malzeme_Kodu = Column(String(50), ForeignKey("Stok.Malzeme_Kodu"), nullable=False, index=True)
    Donem = Column(Integer, nullable=False, index=True)  # YYMM format
    Miktar = Column(DECIMAL(10, 0), nullable=False)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    stok = relationship("Stok", back_populates="stok_sayimlar")
    sube = relationship("Sube", back_populates="stok_sayimlar")

    def __repr__(self):
        return f"<StokSayim {self.Sayim_ID}>"


# ============================================================================
# HR MODELS
# ============================================================================

class Calisan(db.Model):
    """Employee"""
    __tablename__ = "Calisan"
    __table_args__ = {"extend_existing": True}

    TC_No = Column(String(11), primary_key=True, index=True)
    Adi = Column(String(50), nullable=False)
    Soyadi = Column(String(50), nullable=False)
    Hesap_No = Column(String(30), nullable=True)
    IBAN = Column(String(26), nullable=True)
    Net_Maas = Column(DECIMAL(10, 2), nullable=True)
    Sigorta_Giris = Column(Date, nullable=True)
    Sigorta_Cikis = Column(Date, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)

    # Relationships
    sube = relationship("Sube", back_populates="calisanlar")
    puantajlar = relationship("Puantaj", back_populates="calisan")
    avans_istekler = relationship("AvansIstek", back_populates="calisan")

    def __repr__(self):
        return f"<Calisan {self.TC_No}>"


class PuantajSecimi(db.Model):
    """Attendance type/option"""
    __tablename__ = "Puantaj_Secimi"
    __table_args__ = {"extend_existing": True}

    Secim_ID = Column(Integer, primary_key=True, index=True)
    Secim = Column(String(100), nullable=False, unique=True, index=True)
    Degeri = Column(DECIMAL(3, 1), nullable=False)
    Renk_Kodu = Column(String(15), nullable=False)
    Aktif_Pasif = Column(Boolean, default=True, index=True)

    # Relationships
    puantajlar = relationship("Puantaj", back_populates="secim")

    def __repr__(self):
        return f"<PuantajSecimi {self.Secim}>"


class Puantaj(db.Model):
    """Attendance record"""
    __tablename__ = "Puantaj"
    __table_args__ = {"extend_existing": True}

    Puantaj_ID = Column(Integer, primary_key=True, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    TC_No = Column(String(11), ForeignKey("Calisan.TC_No"), nullable=False, index=True)
    Secim_ID = Column(Integer, ForeignKey("Puantaj_Secimi.Secim_ID"), nullable=False, index=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    calisan = relationship("Calisan", back_populates="puantajlar")
    secim = relationship("PuantajSecimi", back_populates="puantajlar")
    sube = relationship("Sube", back_populates="puantajlar")

    def __repr__(self):
        return f"<Puantaj {self.Puantaj_ID}>"


class AvansIstek(db.Model):
    """Employee advance request"""
    __tablename__ = "Avans_Istek"
    __table_args__ = {"extend_existing": True}

    Avans_ID = Column(Integer, primary_key=True, index=True)
    Donem = Column(Integer, nullable=False, index=True)  # YYMM format
    TC_No = Column(String(11), ForeignKey("Calisan.TC_No"), nullable=False, index=True)
    Tutar = Column(DECIMAL(10, 2), nullable=False)
    Aciklama = Column(Text, nullable=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    calisan = relationship("Calisan", back_populates="avans_istekler")
    sube = relationship("Sube", back_populates="avans_istekler")

    def __repr__(self):
        return f"<AvansIstek {self.Avans_ID}>"


class CalisanTalep(db.Model):
    """Employee request (hire/termination)"""
    __tablename__ = "Calisan_Talep"
    __table_args__ = {"extend_existing": True}

    Calisan_Talep_ID = Column(Integer, primary_key=True, autoincrement=True)
    Talep = Column(Enum('İşten Çıkış', 'İşe Giriş'), default='İşe Giriş')
    TC_No = Column(String(11), nullable=False, index=True)
    Adi = Column(String(50), nullable=False)
    Soyadi = Column(String(50), nullable=False)
    Ilk_Soyadi = Column(String(50), nullable=False)
    Hesap_No = Column(String(30), nullable=True)
    IBAN = Column(String(26), nullable=True)
    Ogrenim_Durumu = Column(String(26), nullable=True)
    Cinsiyet = Column(Enum('Erkek', 'Kadın'), default='Erkek')
    Gorevi = Column(String(26), nullable=True)
    Anne_Adi = Column(String(26), nullable=True)
    Baba_Adi = Column(String(26), nullable=True)
    Dogum_Yeri = Column(String(26), nullable=True)
    Dogum_Tarihi = Column(Date, nullable=True)
    Medeni_Hali = Column(Enum('Bekar', 'Evli'), default='Bekar')
    Cep_No = Column(String(16), nullable=True)
    Adres_Bilgileri = Column(String(50), nullable=True)
    Gelir_Vergisi_Matrahi = Column(DECIMAL(15, 2), nullable=True)
    SSK_Cikis_Nedeni = Column(String(50), nullable=True)
    Net_Maas = Column(DECIMAL(10, 2), nullable=True)
    Sigorta_Giris = Column(Date, nullable=True)
    Sigorta_Cikis = Column(Date, nullable=True)
    Is_Onay_Veren_Kullanici_ID = Column(Integer, ForeignKey("Kullanici.Kullanici_ID"), nullable=True, index=True)
    Is_Onay_Tarih = Column(DateTime, nullable=True)
    SSK_Onay_Veren_Kullanici_ID = Column(Integer, ForeignKey("Kullanici.Kullanici_ID"), nullable=True, index=True)
    SSK_Onay_Tarih = Column(DateTime, nullable=True)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Imaj_Adi = Column(String(255), nullable=True)
    Imaj = Column(LargeBinary, nullable=True)
    Kayit_Tarih = Column(DateTime, default=func.now())

    # Relationships
    sube = relationship("Sube", back_populates="calisan_talepler")
    is_onay_veren_kullanici = relationship(
        "Kullanici",
        foreign_keys=[Is_Onay_Veren_Kullanici_ID],
        back_populates="is_onay_veren_talepler"
    )
    ssk_onay_veren_kullanici = relationship(
        "Kullanici",
        foreign_keys=[SSK_Onay_Veren_Kullanici_ID],
        back_populates="ssk_onay_veren_talepler"
    )

    def __repr__(self):
        return f"<CalisanTalep {self.Calisan_Talep_ID}>"


# ============================================================================
# OTHER MODELS
# ============================================================================

class YemekCeki(db.Model):
    """Meal tickets"""
    __tablename__ = "Yemek_Ceki"
    __table_args__ = {"extend_existing": True}

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Kategori_ID = Column(Integer, ForeignKey("Kategori.Kategori_ID"), nullable=False, index=True)
    Tarih = Column(Date, nullable=False, index=True)
    Tutar = Column(DECIMAL(15, 2), nullable=False)
    Odeme_Tarih = Column(Date, nullable=False)
    Ilk_Tarih = Column(Date, nullable=False)
    Son_Tarih = Column(Date, nullable=False)
    Sube_ID = Column(Integer, ForeignKey("Sube.Sube_ID"), nullable=False, index=True)
    Imaj = Column(LargeBinary, nullable=True)
    Imaj_Adi = Column(String(255), nullable=True)
    Kayit_Tarihi = Column(DateTime, default=func.now())

    # Relationships
    kategori = relationship("Kategori")
    sube = relationship("Sube", back_populates="yemek_cekiler")

    def __repr__(self):
        return f"<YemekCeki {self.ID}>"


class Cari(db.Model):
    """Ledger/Customer account"""
    __tablename__ = "Cari"
    __table_args__ = {"extend_existing": True}

    Cari_ID = Column(Integer, primary_key=True, index=True)
    Alici_Unvani = Column(String(200), nullable=False, index=True)
    e_Fatura_Kategori_ID = Column(Integer, nullable=True)
    Referans_ID = Column(Integer, ForeignKey("Odeme_Referans.Referans_ID"), nullable=True, index=True)
    Cari = Column(Boolean, default=True)
    Aciklama = Column(Text, nullable=True)
    Aktif_Pasif = Column(Boolean, default=True, index=True)
    Kayit_Tarihi = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Cari {self.Alici_Unvani}>"


class Mutabakat(db.Model):
    """Reconciliation"""
    __tablename__ = "Mutabakat"
    __table_args__ = {"extend_existing": True}

    Mutabakat_ID = Column(Integer, primary_key=True, index=True)
    Cari_ID = Column(Integer, ForeignKey("Cari.Cari_ID"), nullable=False, index=True)
    Mutabakat_Tarihi = Column(Date, nullable=False, index=True)
    Tutar = Column(DECIMAL(15, 2), nullable=False)

    def __repr__(self):
        return f"<Mutabakat {self.Mutabakat_ID}>"


# Export all models for easy importing
__all__ = [
    "Sube", "Kullanici", "Rol", "Yetki", "KullaniciRol", "RolYetki",
    "Deger", "UstKategori", "Kategori",
    "EFatura", "B2BEkstre", "DigerHarcama", "Odeme", "OdemeReferans",
    "Nakit", "EFaturaReferans", "POSHareketleri",
    "Gelir", "GelirEkstra",
    "Stok", "StokFiyat", "StokSayim",
    "Calisan", "PuantajSecimi", "Puantaj", "AvansIstek", "CalisanTalep",
    "YemekCeki", "Cari", "Mutabakat",
]
