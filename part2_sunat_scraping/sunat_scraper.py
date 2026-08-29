import argparse
import os
import re
import time
from datetime import date

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


URL = "https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias"
START_YEAR = 2024
START_MONTH = 1
OUTPUT_DIR = "output"
OUTPUT_FILE = "tipo_cambio_sunat.csv"
WAIT_SECONDS = 15
PAUSE_BETWEEN_CLICKS = 2

PREV_BUTTON_CLASS = "js-cal-prev"
DAY_CELL_CLASS = "calendar-day"


def parse_amount(text):
    m = re.search(r"(\d+\.\d+)", text)
    return float(m.group(1)) if m else None


def build_driver():
    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Edge(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def months_between(start_year, start_month, end_year, end_month):
    return (end_year - start_year) * 12 + (end_month - start_month)


def scrape_current_month(driver, year, month):
    cells = driver.find_elements(By.CSS_SELECTOR, f".{DAY_CELL_CLASS}")
    registros = []
    for cell in cells:
        text = cell.text.strip()
        if "Compra" not in text or "Venta" not in text:
            continue
        lines = text.split("\n")
        day_number = None
        for line in lines:
            if line.strip().isdigit():
                day_number = int(line.strip())
                break
        if day_number is None:
            continue
        compra = None
        venta = None
        for line in lines:
            if "Compra" in line:
                compra = parse_amount(line)
            if "Venta" in line:
                venta = parse_amount(line)
        if compra is None and venta is None:
            continue
        registros.append({
            "fecha": f"{year:04d}-{month:02d}-{day_number:02d}",
            "compra": compra,
            "venta": venta,
        })
    return registros


def go_to_previous_month(driver, wait):
    old_cells = driver.find_elements(By.CSS_SELECTOR, f".{DAY_CELL_CLASS}")
    prev_button = driver.find_element(By.CSS_SELECTOR, f".{PREV_BUTTON_CLASS}")
    prev_button.click()
    if old_cells:
        try:
            wait.until(EC.staleness_of(old_cells[0]))
        except TimeoutException:
            time.sleep(PAUSE_BETWEEN_CLICKS)
    else:
        time.sleep(PAUSE_BETWEEN_CLICKS)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".{DAY_CELL_CLASS}")))


def main():
    parser = argparse.ArgumentParser(description="Scraper de tipo de cambio SUNAT")
    parser.add_argument("--start-year", type=int, default=START_YEAR)
    parser.add_argument("--start-month", type=int, default=START_MONTH)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    today = date.today()
    n_clicks = months_between(args.start_year, args.start_month, today.year, today.month)

    driver = build_driver()
    wait = WebDriverWait(driver, WAIT_SECONDS)

    todos_los_registros = []
    meses_con_datos = 0
    meses_sin_datos = 0

    try:
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".{DAY_CELL_CLASS}")))

        year, month = today.year, today.month

        for i in range(n_clicks + 1):
            print(f"Leyendo {year}-{month:02d}...")
            registros = scrape_current_month(driver, year, month)
            if registros:
                todos_los_registros.extend(registros)
                meses_con_datos += 1
            else:
                meses_sin_datos += 1
                print(f"  Sin datos visibles para {year}-{month:02d}, se omite.")

            if i < n_clicks:
                try:
                    go_to_previous_month(driver, wait)
                except (TimeoutException, StaleElementReferenceException) as e:
                    print(f"  No se pudo retroceder de mes: {e}")
                    break
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
    finally:
        driver.quit()

    df = pd.DataFrame(todos_los_registros)
    df = df.sort_values("fecha").reset_index(drop=True)
    output_path = os.path.join(args.output_dir, OUTPUT_FILE)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print("\n--- Resumen ---")
    print(f"Meses con datos: {meses_con_datos}")
    print(f"Meses sin datos: {meses_sin_datos}")
    print(f"Total de registros guardados: {len(df)}")
    print(f"Archivo generado: {output_path}")


if __name__ == "__main__":
    main()
