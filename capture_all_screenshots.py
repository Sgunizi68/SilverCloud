import asyncio
import os
import sys
from playwright.async_api import async_playwright

OUTPUT_DIR = r"C:\Users\sg.msa\.gemini\antigravity-ide\brain\e17606ba-f4c6-49b4-9d85-9d07cfb90911"
BASE_URL = "http://localhost:5000"

PAGES = [
    ("login", "/login"),
    ("dashboard", "/dashboard"),
    ("subeler", "/subeler"),
    ("degerler", "/degerler"),
    ("kullanicilar", "/kullanicilar"),
    ("roller", "/roller"),
    ("yetkiler", "/yetkiler"),
    ("kullanici_rol_atamalari", "/kullanici-rol-atamalari"),
    ("rol_yetki_atamalari", "/rol-yetki-atamalari"),
    ("efatura_referans_yonetimi", "/efatura-referans-yonetimi"),
    ("odeme_referans_yonetimi", "/odeme-referans-yonetimi"),
    ("gelir_referans_yonetimi", "/gelir-referans-yonetimi"),
    ("cari_borc_yonetimi", "/cari-borc-yonetimi"),
    ("ust_kategori_yonetimi", "/ust-kategori-yonetimi"),
    ("kategori_yonetimi", "/kategori-yonetimi"),
    ("fatura_yukleme", "/fatura-yukleme"),
    ("fatura_kategori_atama", "/fatura-kategori-atama"),
    ("b2b_ekstre_yukleme", "/b2b-ekstre-yukleme"),
    ("fatura_bolme_yonetimi", "/fatura-bolme-yonetimi"),
    ("mutabakat_yonetimi", "/mutabakat-yonetimi"),
    ("odeme_yukleme", "/odeme-yukleme"),
    ("odeme_kategori_atama", "/odeme-kategori-atama"),
    ("diger_harcamalar", "/diger-harcamalar"),
    ("pos_hareketleri_yukleme", "/pos-hareketleri-yukleme"),
    ("robotpos-gelir-yukleme", "/robotpos-gelir-yukleme"),
    ("tabak_sayisi_yukleme", "/tabak-sayisi-yukleme"),
    ("yemek_ceki", "/yemek-ceki"),
    ("gelir_girisi", "/gelir-girisi"),
    ("nakit_girisi", "/nakit-girisi"),
    ("stok_tanimlama", "/stok-tanimlama"),
    ("stok_fiyat_tanimlama", "/stok-fiyat-tanimlama"),
    ("stok_sayimi", "/stok-sayimi"),
    ("calisanlar", "/calisanlar"),
    ("puantaj_secim_yonetimi", "/puantaj-secim-yonetimi"),
    ("puantaj_girisi", "/puantaj-girisi"),
    ("avans_talepleri", "/avans-talepleri"),
    ("calisan_talep_yonetimi", "/calisan-talep-yonetimi"),
    ("nakit_yatirma_kontrol_raporu", "/nakit-yatirma-kontrol-raporu"),
    ("odeme_raporu", "/odeme-rapor"),
    ("fatura_raporu", "/fatura-rapor"),
    ("fatura_diger_harcama_raporu", "/fatura-diger-harcama-rapor"),
    ("pos_kontrol_dashboard", "/pos-kontrol-dashboard"),
    ("online_kontrol_dashboard", "/online-kontrol-dashboard"),
    ("yemek_ceki_kontrol_dashboard", "/yemek-ceki-kontrol-dashboard"),
    ("vps_dashboard", "/vps-dashboard"),
    ("bayi_karlilik_raporu", "/bayi-karlilik-raporu"),
    ("ozet_kontrol_raporu", "/ozet-kontrol-raporu"),
    ("nakit_akis_gelir_raporu", "/nakit-akis-gelir-raporu"),
]

async def do_login(page):
    await page.goto(f"{BASE_URL}/login")
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'Adm123!')
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    return "/login" not in page.url

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Persistent context to keep session
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Login
        print("Logging in...")
        if not await do_login(page):
            print("Login failed! Aborting.")
            await browser.close()
            return

        print("Login successful. Starting captures...")

        for name, path in PAGES:
            try:
                print(f"Capturing {name} ({path})...")
                # For login page itself, capture before any redirects
                if name == "login":
                    # Create a new context and page to capture login without session
                    login_context = await browser.new_context(viewport={"width": 1440, "height": 900})
                    login_page = await login_context.new_page()
                    await login_page.goto(f"{BASE_URL}/login")
                    await login_page.wait_for_load_state("networkidle")
                    out_path = os.path.join(OUTPUT_DIR, f"{name}.png")
                    await login_page.screenshot(path=out_path)
                    await login_context.close()
                    print(f"  -> Saved login page to {out_path}")
                    continue

                await page.goto(f"{BASE_URL}{path}")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2.5) # Wait for animations and tables to render

                # Re-login if session lost
                if "/login" in page.url:
                    print("  Session lost. Re-logging in...")
                    if not await do_login(page):
                        print(f"  Re-login failed for {name}. Skipping.")
                        continue
                    await page.goto(f"{BASE_URL}{path}")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2.5)

                out_path = os.path.join(OUTPUT_DIR, f"{name}.png")
                await page.screenshot(path=out_path)
                print(f"  -> Saved: {out_path}")
            except Exception as e:
                print(f"  -> ERROR for {name}: {e}")

        await context.close()
        await browser.close()
        print("All screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(capture_all())
