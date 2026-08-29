import argparse
import os
import time
from datetime import date

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


URL = "https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias"
START_YEAR = 2024
START_MONTH = 1
OUTPUT_DIR = "output"
OUTPUT_FILE = "tipo_cambio_sunat.csv"
WAIT_SECONDS = 15
PAUSE_BETWEEN_REQUESTS = 2

SELECT_MES_ID = "TODO_id_del_select_de_mes"
SELECT_ANIO_ID = "TODO_id_del_select_de_anio"
BOTON_BUSCAR_ID = "TODO_id_o_texto_del_boton_buscar"
TABLA_RESULTADOS_ID = "TODO_id_de_la_tabla_resultados"


def build_driver():
    """Configura y devuelve el navegador controlado por Selenium."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def month_year_range(start_year: int, start_month: int):
    """Genera tuplas (anio, mes) desde el inicio hasta el mes actual, inclusive."""
    today = date.today()
    year, month = start_year, start_month
    while (year, month) <= (today.year, today.month):
        yield year, month
        month += 1
        if month > 12:
            month = 1
            year += 1


def scrape_month(driver, wait, year: int, month: int) -> list:
    """
    Consulta un mes/anio especifico en el formulario de SUNAT y devuelve
    una lista de diccionarios con fecha, compra y venta para ese mes.
    Si el mes no tiene datos publicados, devuelve una lista vacia (no falla).
    """
    driver.get(URL)

    try:
        select_mes_el = wait.until(EC.presence_of_element_located((By.ID, SELECT_MES_ID)))
        select_anio_el = wait.until(EC.presence_of_element_located((By.ID, SELECT_ANIO_ID)))

        Select(select_mes_el).select_by_value(str(month))
        Select(select_anio_el).select_by_value(str(year))

        boton = wait.until(EC.element_to_be_clickable((By.ID, BOTON_BUSCAR_ID)))
        boton.click()

        tabla = wait.until(EC.presence_of_element_located((By.ID, TABLA_RESULTADOS_ID)))

        filas = tabla.find_elements(By.TAG_NAME, "tr")
        registros = []
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) < 3:
                continue
            fecha_txt = celdas[0].text.strip()
            compra_txt = celdas[1].text.strip()
            venta_txt = celdas[2].text.strip()
            if not fecha_txt:
                continue
            registros.append({
                "fecha": fecha_txt,
                "compra": compra_txt,
                "venta": venta_txt,
            })
        return registros

    except TimeoutException:
        print(f"  [{year}-{month:02d}] Sin datos publicados o la pagina no cargo a tiempo. Se omite.")
        return []
    except NoSuchElementException:
        print(f"  [{year}-{month:02d}] No se encontro un elemento esperado. Revisa los selectores TODO.")
        return []


def main():
    parser = argparse.ArgumentParser(description="Scraper de tipo de cambio SUNAT")
    parser.add_argument("--start-year", type=int, default=START_YEAR)
    parser.add_argument("--start-month", type=int, default=START_MONTH)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    if "TODO" in SELECT_MES_ID or "TODO" in SELECT_ANIO_ID or "TODO" in BOTON_BUSCAR_ID or "TODO" in TABLA_RESULTADOS_ID:
        print("ERROR: Todavia no completaste los selectores TODO al inicio del archivo.")
        print("Revisa las instrucciones del chat para conseguirlos con el Inspector del navegador.")
        return

    os.makedirs(args.output_dir, exist_ok=True)

    driver = build_driver()
    wait = WebDriverWait(driver, WAIT_SECONDS)

    todos_los_registros = []
    meses_procesados = 0
    meses_sin_datos = 0

    try:
        for year, month in month_year_range(args.start_year, args.start_month):
            print(f"Consultando {year}-{month:02d}...")
            registros = scrape_month(driver, wait, year, month)
            if registros:
                for r in registros:
                    r["anio"] = year
                    r["mes"] = month
                todos_los_registros.extend(registros)
                meses_procesados += 1
            else:
                meses_sin_datos += 1
            time.sleep(PAUSE_BETWEEN_REQUESTS)
    finally:
        driver.quit()

    df = pd.DataFrame(todos_los_registros)
    output_path = os.path.join(args.output_dir, OUTPUT_FILE)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print("\n--- Resumen ---")
    print(f"Meses con datos: {meses_procesados}")
    print(f"Meses sin datos / omitidos: {meses_sin_datos}")
    print(f"Total de registros guardados: {len(df)}")
    print(f"Archivo generado: {output_path}")


if __name__ == "__main__":
    main()
