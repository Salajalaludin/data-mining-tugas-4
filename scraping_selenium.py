from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.scrapethissite.com/pages/forms/"
KATA_KUNCI = "kings"
FOLDER_HASIL = Path(__file__).resolve().parent / "hasil_scraping"
FOLDER_HASIL.mkdir(parents=True, exist_ok=True)

def ambil_teks(baris, selektor):
    # Baca teks sel sesuai class CSS, kosong menjadi None
    hasil = baris.find_element(By.CSS_SELECTOR, selektor).text.strip()
    return hasil if hasil else None


def main():
    # Selenium modern mengelola ChromeDriver secara otomatis jika diperlukan.
    driver = webdriver.Chrome()
    try:
        tunggu = WebDriverWait(driver, 20)

        # Buka situs dan temukan kotak pencarian (id="q").
        driver.get(URL)
        kotak = tunggu.until(EC.element_to_be_clickable((By.ID, "q")))

        # Isi form dengan kata kunci dari materi: "kings".
        kotak.clear()
        kotak.send_keys(KATA_KUNCI)
        driver.save_screenshot(str(FOLDER_HASIL / "01_form_pencarian.png"))

        # Klik tombol Search.
        tombol = tunggu.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"]'))
        )
        tombol.click()

        # Tunggu hasil pencarian, bukan menggunakan sleep yang kaku.
        tunggu.until(EC.url_contains("q="))
        tabel = tunggu.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "table.table"))
        )
        baris_hasil = tunggu.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "table.table tbody tr.team")
            )
        )

        # Dokumentasi: hasil seluruh jendela dan tabel saja.
        driver.save_screenshot(str(FOLDER_HASIL / "02_hasil_pencarian.png"))
        tabel.screenshot(str(FOLDER_HASIL / "03_tabel.png"))

        # Ekstrak sembilan variabel dari setiap baris HTML.
        data = []
        for baris in baris_hasil:
            data.append(
                {
                    "team_name": ambil_teks(baris, "td.name"),
                    "year": ambil_teks(baris, "td.year"),
                    "wins": ambil_teks(baris, "td.wins"),
                    "losses": ambil_teks(baris, "td.losses"),
                    "ot_losses": ambil_teks(baris, "td.ot-losses"),
                    "win_pct": ambil_teks(baris, "td.pct"),
                    "goals_for": ambil_teks(baris, "td.gf"),
                    "goals_against": ambil_teks(baris, "td.ga"),
                    "goal_difference": ambil_teks(baris, "td.diff"),
                }
            )

        # Bentuk tidy data: satu baris per tim-tahun, satu kolom per variabel.
        df = pd.DataFrame(data)
        for kolom in (
            "year", "wins", "losses", "ot_losses", "goals_for",
            "goals_against", "goal_difference",
        ):
            df[kolom] = pd.to_numeric(df[kolom], errors="coerce").astype("Int64")
        df["win_pct"] = pd.to_numeric(df["win_pct"], errors="coerce")

        lokasi_csv = FOLDER_HASIL / "nhl_kings.csv"
        df.to_csv(lokasi_csv, index=False, encoding="utf-8-sig")

        print(f"URL hasil      : {driver.current_url}")
        print(f"Jumlah baris   : {len(df)}")
        print(f"Jumlah kolom   : {len(df.columns)}")
        print(f"Lokasi CSV     : {lokasi_csv}")
        print("\nContoh lima observasi pertama:\n")
        print(df.head().to_string(index=False))

    finally:
        # Browser tetap ditutup walaupun scraping gagal.
        driver.quit()

if __name__ == "__main__":
    main()

