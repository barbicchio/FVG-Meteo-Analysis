import time
import json
import urllib.parse
from io import StringIO
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


URL = "https://www.meteo.fvg.it/archivio.php?ln=&p=dati"


def wait_years_refresh(driver, wait):
    """Aspetta che il select anni abbia almeno 1 option non disabled."""
    wait.until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#anno option:not([disabled])")) > 0
    )


def get_enabled_years_xpath(driver) -> list[int]:
    """Prende SOLO anni non disabled, leggendo direttamente dal DOM aggiornato."""
    opts = driver.find_elements(By.CSS_SELECTOR, "#anno option:not([disabled])")
    years = []
    for o in opts:
        v = (o.get_attribute("value") or "").strip()
        if v.isdigit():
            years.append(int(v))
    return sorted(set(years))


def load_station_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_station_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def accept_cookies_if_present(driver, wait):
    try:
        modal = wait.until(
            EC.presence_of_element_located((By.ID, "cookieModal"))
        )
        ok_btn = modal.find_element(By.ID, "ok")
        ok_btn.click()
        wait.until(EC.invisibility_of_element(modal))
        print("✔ Cookie modal accettato")
    except Exception:
        print("ℹ Cookie modal non presente")


def build_driver(headless: bool = True) -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1200,900")
    return webdriver.Chrome(options=opts)


def scrape_station_monthly(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    station: str,
    months,
    out_path: Path,
    rate_limit: int = 3,
):
    """
    Scrape dati giornalieri (CSV) per una singola stazione.
    Se disponibile, usa 'mese = Tutti' per fare 1 richiesta per anno.
    Salva incrementale su JSON per anno.
    """

    # seleziona stazione UNA volta
    Select(driver.find_element(By.ID, "stazione")).select_by_visible_text(station)

    # aspetta refresh anni
    wait_years_refresh(driver, wait)

    available_years = get_enabled_years_xpath(driver)
    print(
        f"Anni disponibili per {station}: "
        f"{available_years[0]}..{available_years[-1]} ({len(available_years)})"
    )

    # carica eventuale JSON già esistente
    station_data = load_station_json(out_path)

    # prova a scoprire il value di "Tutti" (una volta, dopo che il DOM è pronto)
    all_month_value = 99
    if all_month_value is not None:
        print(f"✔ Opzione mese 'Tutti' rilevata: value={all_month_value!r} (1 richiesta/anno)")
    else:
        print("ℹ Opzione mese 'Tutti' non trovata: fallback a 12 mesi")

    for year in tqdm(available_years, desc=f"{station} – anni", leave=True):
        year_key = str(year)

        if year_key in station_data:
            print(f"⏭️ {station} {year} già presente, skip")
            continue

        year_dfs = []

        # --- CASO 1: mese = TUTTI (1 richiesta per anno) ---
        if all_month_value is not None:
            Select(driver.find_element(By.ID, "anno")).select_by_visible_text(str(year))
            Select(driver.find_element(By.ID, "mese")).select_by_value(str(all_month_value))

            driver.find_element(By.ID, "giornalieri").click()

            chk = driver.find_element(By.ID, "confnote")
            if not chk.is_selected():
                chk.click()

            driver.find_element(By.ID, "visualizza").click()
            time.sleep(2)

            try:
                csv_link = wait.until(
                    EC.presence_of_element_located((By.ID, "salvaDati"))
                )
            except Exception:
                print(f"  ⚠️ Nessun dato (tutti i mesi) per {station} {year}")
                continue

            csv_href = csv_link.get_attribute("href")
            csv_text = urllib.parse.unquote(csv_href.split(",", 1)[1])

            df = pd.read_csv(StringIO(csv_text), sep=";")
            df["anno"] = year
            # NOTA: in modalità "tutti", il CSV dovrebbe già contenere la data/giorno/mese.
            # Non forziamo df["mese"] qui, perché rischi di sovrascrivere un campo già presente.
            df["stazione"] = station

            year_dfs.append(df)
            time.sleep(rate_limit)

        # --- CASO 2: fallback 12 mesi ---
        else:
            for month in tqdm(months, desc=f"{station} {year} – mesi", leave=False):
                Select(driver.find_element(By.ID, "anno")).select_by_visible_text(str(year))
                Select(driver.find_element(By.ID, "mese")).select_by_value(str(month))

                driver.find_element(By.ID, "giornalieri").click()

                chk = driver.find_element(By.ID, "confnote")
                if not chk.is_selected():
                    chk.click()

                driver.find_element(By.ID, "visualizza").click()
                time.sleep(2)

                try:
                    csv_link = wait.until(
                        EC.presence_of_element_located((By.ID, "salvaDati"))
                    )
                except Exception:
                    continue

                csv_href = csv_link.get_attribute("href")
                csv_text = urllib.parse.unquote(csv_href.split(",", 1)[1])

                df = pd.read_csv(StringIO(csv_text), sep=";")
                df["anno"] = year
                df["mese"] = month
                df["stazione"] = station

                year_dfs.append(df)
                time.sleep(rate_limit)

        if not year_dfs:
            print(f"⚠️ Nessun dato per {station} {year}")
            continue

        year_df = pd.concat(year_dfs, ignore_index=True)

        # salva anno come lista di record
        station_data[year_key] = year_df.to_dict(orient="records")
        save_station_json(out_path, station_data)

        print(f"✔ Salvato {station} {year} ({len(year_df)} record)")


def scrape_stations(
    stations: list[str],
    months,
    out_dir: Path,
    rate_limit: int = 3,
    headless: bool = True,
):
    """
    Scrape più stazioni, salvando un JSON per ciascuna.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    driver = build_driver(headless=headless)
    wait = WebDriverWait(driver, 15)

    driver.get(URL)
    wait.until(EC.presence_of_element_located((By.ID, "anno")))
    accept_cookies_if_present(driver, wait)

    for station in tqdm(stations, desc="Stazioni"):
        print(f"\n▶ Scraping stazione: {station}")

        out_path = out_dir / f"meteo_{station.lower().replace(' ', '_')}.json"

        scrape_station_monthly(
            driver=driver,
            wait=wait,
            station=station,
            months=months,
            out_path=out_path,
            rate_limit=rate_limit,
        )

    driver.quit()


if __name__ == "__main__":
    STATIONS = ["Monte Lussari", "Monte Matajur", "Piancavallo", "Tarvisio Meteo"]  # estendibile
    MONTHS = range(1, 13)

    scrape_stations(
        stations=STATIONS,
        months=MONTHS,
        out_dir=Path("../data/raw/arpa"),
        rate_limit=3,
        headless=True,
    )