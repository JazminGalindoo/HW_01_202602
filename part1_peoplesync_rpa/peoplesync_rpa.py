import argparse
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException
)


FORM_URL = "https://the-paul2002.github.io/Proyecto-IA-/Homework1/"
INPUT_FILE = "empleados.xlsx"
OUTPUT_DIR = "output"
WAIT_SECONDS = 10

COLUMNAS = {
    "nombres": "nombres",
    "dni": "dni",
    "fecha_nacimiento": "fecha_nacimiento",
    "genero": "genero",
    "telefono": "telefono",
    "correo": "correo",
    "area": "area",
    "puesto": "puesto",
    "tipo_contrato": "tipo_contrato",
    "sede": "sede",
    "fecha_ingreso": "fecha_ingreso",
    "modalidad": "modalidad",
}


def find_input_by_label(driver, label_text):
    """Busca un <input> ubicado cerca de un <label> que contenga cierto texto."""
    xpath = (
        f"//label[contains(normalize-space(.), \"{label_text}\")]"
        f"/following::input[1]"
    )
    return driver.find_element(By.XPATH, xpath)


def find_select_by_label(driver, label_text):
    """Busca un <select> ubicado cerca de un <label> que contenga cierto texto."""
    xpath = (
        f"//label[contains(normalize-space(.), \"{label_text}\")]"
        f"/following::select[1]"
    )
    return driver.find_element(By.XPATH, xpath)


def fill_text(driver, label_text, value):
    el = find_input_by_label(driver, label_text)
    el.clear()
    el.send_keys(str(value))


def select_option(driver, label_text, visible_text):
    el = find_select_by_label(driver, label_text)
    Select(el).select_by_visible_text(visible_text)


def click_by_text(driver, text):
    """Hace click en cualquier elemento clickeable que contenga el texto dado."""
    xpath = f"//*[self::button or self::a or self::div][contains(normalize-space(.), \"{text}\")]"
    el = driver.find_element(By.XPATH, xpath)
    el.click()


def fill_record(driver, wait, row: dict) -> tuple:
    """
    Llena el formulario con un registro. Devuelve (exito: bool, mensaje: str).
    """
    try:
        driver.get(FORM_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

        fill_text(driver, "Apellidos y Nombres", row["nombres"])
        fill_text(driver, "N° Documento", row["dni"])
        fill_text(driver, "Fecha de Nacimiento", row["fecha_nacimiento"])
        select_option(driver, "Género", row["genero"])
        fill_text(driver, "Teléfono", row["telefono"])
        fill_text(driver, "Correo Electrónico", row["correo"])

        select_option(driver, "Área", row["area"])
        select_option(driver, "Puesto", row["puesto"])
        select_option(driver, "Tipo de Contrato", row["tipo_contrato"])
        select_option(driver, "Sede", row["sede"])
        fill_text(driver, "Fecha de Ingreso", row["fecha_ingreso"])
        click_by_text(driver, row["modalidad"])

        click_by_text(driver, "Registrar Ingreso")

        time.sleep(1.5)

        errores = driver.find_elements(
            By.XPATH, "//*[contains(text(), 'válido') or contains(text(), 'obligatorio')]"
        )
        errores_visibles = [e.text for e in errores if e.is_displayed() and e.text.strip()]
        if errores_visibles:
            return False, f"Errores de validacion: {errores_visibles}"

        return True, "OK"

    except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
        return False, f"No se pudo interactuar con un campo: {e}"


def main():
    parser = argparse.ArgumentParser(description="RPA para registro en PeopleSync")
    parser.add_argument("--input-file", default=INPUT_FILE)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if not os.path.exists(args.input_file):
        print(f"ERROR: no se encontro el archivo de entrada '{args.input_file}'.")
        print("Descarga el Google Sheet de empleados como Excel y ponlo en esta carpeta.")
        return

    df = pd.read_excel(args.input_file) if args.input_file.endswith((".xlsx", ".xls")) else pd.read_csv(args.input_file)
    df = df.rename(columns={v: k for k, v in COLUMNAS.items()})

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, WAIT_SECONDS)

    exitosos = []
    fallidos = []

    try:
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            print(f"Procesando registro {idx + 1}/{len(df)}: {row_dict.get('nombres', '')}")
            ok, mensaje = fill_record(driver, wait, row_dict)
            if ok:
                exitosos.append(idx)
            else:
                fallidos.append({"indice": idx, "dni": row_dict.get("dni"), "error": mensaje})
                print(f"  -> FALLO: {mensaje}")
    finally:
        driver.quit()

    print("\n--- Resumen final ---")
    print(f"Total procesados: {len(df)}")
    print(f"Exitosos: {len(exitosos)}")
    print(f"Fallidos: {len(fallidos)}")
    for f in fallidos:
        print(f"  - Registro {f['indice']} (DNI {f['dni']}): {f['error']}")

    pd.DataFrame(fallidos).to_csv(os.path.join(args.output_dir, "registros_fallidos.csv"), index=False)
    print(f"\nDetalle de fallidos guardado en {args.output_dir}/registros_fallidos.csv")


if __name__ == "__main__":
    main()
