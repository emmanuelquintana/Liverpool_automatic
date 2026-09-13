import argparse
import getpass
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    DEFAULT_BASE_DIR,
    DEFAULT_EDGE_PROFILE_NAME,
    DEFAULT_EDGE_USER_DATA_DIR,
    DEFAULT_FALLBACK_DRIVER,
    DEFAULT_TIMEOUT,
)
from models import AppConfig
from services import LiverpoolService
from settings import load_settings


BILLS_URL = "https://marketplace.liverpool.com.mx/orders/bills"
MARKETPLACE_BASE_URL = "https://marketplace.liverpool.com.mx"

EXPECTED_BILL_HEADERS = [
    "Fecha de solicitud",
    "Tienda",
    "Pedido",
    "Estado de la solicitud",
    "Fecha limite",
    "Tiempo de respuesta",
    "Correo electronico",
    "RFC",
]

EXCEL_COLUMNS = [
    ("fecha_solicitud", "Fecha de solicitud"),
    ("tienda", "Tienda"),
    ("pedido", "Pedido"),
    ("estado_solicitud", "Estado de la solicitud"),
    ("fecha_limite", "Fecha limite"),
    ("tiempo_respuesta", "Tiempo de respuesta"),
    ("correo_electronico", "Correo tabla"),
    ("rfc", "RFC tabla"),
    ("tipo_de_persona", "Tipo de persona"),
    ("rfc_facturacion", "RFC facturacion"),
    ("nombre_completo", "Nombre completo"),
    ("codigo_postal_del_domicilio_fiscal", "CP fiscal"),
    ("correo_electronico_facturacion", "Correo facturacion"),
    ("regimen_fiscal", "Regimen fiscal"),
    ("uso_de_cfdi", "Uso de CFDI"),
    ("metodo_de_pago", "Metodo de pago"),
    ("forma_de_pago", "Forma de pago"),
    ("url", "URL"),
    ("detalle_error", "Error detalle"),
]


def normalize_text(value: str) -> str:
    return " ".join((value or "").split())


def ascii_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def cli_input(label: str, placeholder: str = "", input_type: str = "text") -> str:
    prompt = f"{label}"
    if placeholder:
        prompt += f" ({placeholder})"
    prompt += ": "
    if input_type == "password":
        return getpass.getpass(prompt)
    return input(prompt)


def build_config(args: argparse.Namespace) -> AppConfig:
    saved = load_settings()
    output_base = Path(args.output_dir or saved.get("base_dir", str(DEFAULT_BASE_DIR)))
    edge_user_data_dir = Path(
        args.edge_user_data_dir
        or saved.get("edge_user_data_dir", str(DEFAULT_EDGE_USER_DATA_DIR))
    )

    return AppConfig(
        base_dir=output_base,
        edge_user_data_dir=edge_user_data_dir,
        edge_profile_name=DEFAULT_EDGE_PROFILE_NAME,
        timeout=int(args.timeout or saved.get("timeout", DEFAULT_TIMEOUT)),
        fallback_driver=args.fallback_driver
        or saved.get("fallback_driver", DEFAULT_FALLBACK_DRIVER),
        overwrite_outputs=True,
        headless=bool(args.headless),
    )


def wait_for_bills_table(driver, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    wait.until(
        lambda d: len(d.find_elements(By.XPATH, "//table//tbody//tr")) > 0
        or "0 - 0" in d.page_source
    )


def set_page_size(driver, page_size: int, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    combo_xpath = (
        "("
        "//div[@role='combobox' and "
        "("
        "contains(@class,'MuiTablePagination-select') or "
        "ancestor::*[contains(@class,'MuiTablePagination-root')]"
        ")"
        "])[1]"
    )

    try:
        combo = wait.until(EC.presence_of_element_located((By.XPATH, combo_xpath)))
    except TimeoutException:
        combo = find_page_size_combo_with_js(driver)
        if combo is None:
            raise TimeoutException(
                "No se encontro el combo de 'Resultados por pagina'."
            )

    current = normalize_text(combo.text or combo.get_attribute("textContent") or "")

    if current == str(page_size):
        print(f"[INFO] Resultados por pagina ya esta en {page_size}.")
        return

    old_signature = table_signature(driver)
    open_page_size_menu(driver, combo, page_size)
    option = wait_for_page_size_option(driver, page_size, timeout)

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
    try:
        ActionChains(driver).move_to_element(option).click().perform()
    except Exception:
        driver.execute_script("arguments[0].click();", option)

    wait.until(
        lambda d: table_signature(d) != old_signature
        or any(
            str(page_size)
            == normalize_text(c.text or c.get_attribute("textContent") or "")
            for c in d.find_elements(By.XPATH, combo_xpath)
        )
    )
    time.sleep(1)
    print(f"[INFO] Se selecciono {page_size} resultados por pagina.")


def open_page_size_menu(driver, combo, page_size: int) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)
    clickable = driver.execute_script(
        "return arguments[0].closest('.MuiInputBase-root') || arguments[0];",
        combo,
    )

    attempts = [
        lambda: ActionChains(driver).move_to_element(clickable).click().perform(),
        lambda: combo.click(),
        lambda: driver.execute_script("arguments[0].click();", clickable),
        lambda: combo.send_keys(Keys.ENTER),
        lambda: combo.send_keys(Keys.SPACE),
        lambda: combo.send_keys(Keys.ARROW_DOWN),
    ]

    for attempt in attempts:
        try:
            attempt()
            time.sleep(0.5)
            if find_page_size_option_with_js(driver, page_size) is not None:
                return
        except Exception:
            continue

    raise TimeoutException(
        f"No se pudo abrir el menu de resultados por pagina para elegir {page_size}."
    )


def wait_for_page_size_option(driver, page_size: int, timeout: int):
    wait = WebDriverWait(driver, timeout)
    option_xpath = (
        f"//li[@role='option' and "
        f"(@data-value='{page_size}' or normalize-space(.)='{page_size}')]"
    )
    try:
        return wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
    except TimeoutException:
        option = find_page_size_option_with_js(driver, page_size)
        if option is None:
            raise TimeoutException(
                f"No se encontro la opcion de paginado {page_size}."
            )
        return option


def find_page_size_combo_with_js(driver):
    return driver.execute_script(
        """
        const norm = (value) => (value || "").replace(/\\s+/g, " ").trim();
        const candidates = Array.from(
          document.querySelectorAll("div[role='combobox'], .MuiTablePagination-select")
        );
        return candidates.find((element) => {
          const text = norm(element.textContent);
          const pagination = element.closest(".MuiTablePagination-root");
          const toolbarText = norm(element.closest(".MuiToolbar-root")?.textContent);
          return (
            /^\\d+$/.test(text) &&
            (pagination ||
              element.className.includes("MuiTablePagination-select") ||
              toolbarText.includes("Resultados por pagina") ||
              toolbarText.includes("Resultados por página"))
          );
        }) || null;
        """
    )


def find_page_size_option_with_js(driver, page_size: int):
    return driver.execute_script(
        """
        const expected = String(arguments[0]);
        return Array.from(document.querySelectorAll("li[role='option']")).find((element) => {
          const text = (element.textContent || "").replace(/\\s+/g, " ").trim();
          return element.getAttribute("data-value") === expected || text === expected;
        }) || null;
        """,
        page_size,
    )


def table_signature(driver) -> str:
    rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
    values = []
    for row in rows[:3]:
        values.append(normalize_text(row.text))
    return "|".join(values)


def get_headers(driver) -> List[str]:
    headers = [
        normalize_text(cell.text)
        for cell in driver.find_elements(By.XPATH, "//table//thead//th")
    ]
    headers = [h for h in headers if h]
    return headers or EXPECTED_BILL_HEADERS


def extract_bill_rows_from_current_page(driver, page_index: int) -> List[Dict[str, Any]]:
    headers = get_headers(driver)
    rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
    records: List[Dict[str, Any]] = []

    for row in rows:
        cells = row.find_elements(By.XPATH, "./th|./td")
        if not cells:
            continue

        values = [normalize_text(cell.text) for cell in cells]
        record: Dict[str, Any] = {"pagina": page_index}
        for index, value in enumerate(values):
            header = headers[index] if index < len(headers) else f"columna_{index + 1}"
            record[ascii_key(header)] = value

        try:
            link = row.find_element(By.XPATH, './/a[contains(@href,"/orders/detail/")]')
            href = link.get_attribute("href") or ""
            record["url"] = urljoin(MARKETPLACE_BASE_URL, href)
            record["pedido"] = normalize_text(link.text) or extract_order_id(href)
        except Exception:
            record.setdefault("url", "")
            record.setdefault("pedido", "")

        records.append(record)

    return records


def extract_order_id(value: str) -> str:
    match = re.search(r"/orders/detail/(\d+)", value or "")
    return match.group(1) if match else ""


def get_enabled_next_button(driver):
    buttons = driver.find_elements(By.XPATH, "//button[@aria-label='next page']")
    for button in buttons:
        if button.is_enabled():
            return button
    return None


def collect_all_bills(driver, timeout: int, max_pages: int) -> List[Dict[str, Any]]:
    all_records: List[Dict[str, Any]] = []
    seen_keys = set()
    page_index = 1

    while page_index <= max_pages:
        wait_for_bills_table(driver, timeout)
        page_records = extract_bill_rows_from_current_page(driver, page_index)

        new_records = []
        for record in page_records:
            key = (
                record.get("pedido", ""),
                record.get("fecha_solicitud", ""),
                record.get("rfc", ""),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            all_records.append(record)
            new_records.append(record)

        print(
            f"[INFO] Pagina {page_index}: {len(page_records)} filas, "
            f"{len(new_records)} nuevas."
        )

        next_button = get_enabled_next_button(driver)
        if not next_button:
            break

        old_signature = table_signature(driver)
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", next_button
        )
        driver.execute_script("arguments[0].click();", next_button)
        WebDriverWait(driver, timeout).until(
            lambda d: table_signature(d) != old_signature
        )
        time.sleep(1)
        page_index += 1

    if page_index > max_pages:
        print(f"[WARN] Se alcanzo el maximo de paginas ({max_pages}).")

    return all_records


def click_facturacion_tab(driver, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    tab = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@role='tab' and normalize-space(.)='Facturación']",
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tab)
    driver.execute_script("arguments[0].click();", tab)


def extract_billing_data(driver, timeout: int) -> Dict[str, str]:
    wait = WebDriverWait(driver, timeout)
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[class*='BillingData_container']")
        )
    )

    data = driver.execute_script(
        """
        const pairs = {};
        const boxes = Array.from(
          document.querySelectorAll("[class*='BillingData_container'] [class*='css-18467a']")
        );
        for (const box of boxes) {
          const paragraphs = Array.from(box.querySelectorAll("p"))
            .map((node) => (node.innerText || "").trim())
            .filter(Boolean);
          if (paragraphs.length >= 2) {
            pairs[paragraphs[0]] = paragraphs.slice(1).join(" ");
          }
        }
        if (Object.keys(pairs).length) return pairs;

        const fields = Array.from(
          document.querySelectorAll("[class*='BillingData_field']")
        );
        for (const field of fields) {
          let sibling = field.nextElementSibling;
          while (sibling && !(sibling.innerText || "").trim()) {
            sibling = sibling.nextElementSibling;
          }
          if (sibling) {
            pairs[(field.innerText || "").trim()] = (sibling.innerText || "").trim();
          }
        }
        return pairs;
        """
    )
    return {normalize_text(k): normalize_text(v) for k, v in (data or {}).items()}


def enrich_with_order_billing_data(
    driver,
    service: LiverpoolService,
    records: List[Dict[str, Any]],
    timeout: int,
    limit: int | None,
    json_path: Path,
) -> None:
    total = len(records) if limit is None else min(limit, len(records))

    for index, record in enumerate(records[:total], start=1):
        pedido = record.get("pedido") or extract_order_id(record.get("url", ""))
        url = record.get("url")
        print(f"[INFO] Facturacion {index}/{total}: pedido {pedido}")

        if not url:
            record["detalle_error"] = "Sin URL de detalle"
            continue

        try:
            driver.get(url)
            service._check_and_handle_login(driver)
            click_facturacion_tab(driver, timeout)
            billing_data = extract_billing_data(driver, timeout)
            record["billing_data"] = billing_data
            for label, value in billing_data.items():
                key = ascii_key(label)
                if key == "rfc":
                    key = "rfc_facturacion"
                elif key == "correo_electronico":
                    key = "correo_electronico_facturacion"
                record[key] = value
            record["detalle_error"] = ""
        except TimeoutException as exc:
            record["detalle_error"] = f"Timeout leyendo facturacion: {exc}"
        except Exception as exc:
            record["detalle_error"] = f"Error leyendo facturacion: {exc}"

        save_json(records, json_path)


def save_json(records: List[Dict[str, Any]], path: Path) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": BILLS_URL,
        "total_facturas": len(records),
        "facturas": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def save_excel(records: List[Dict[str, Any]], path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Facturacion"

    header_fill = PatternFill("solid", fgColor="7A1739")
    header_font = Font(color="FFFFFF", bold=True)

    sheet.append([label for _, label in EXCEL_COLUMNS])
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font

    for record in records:
        sheet.append([record.get(key, "") for key, _ in EXCEL_COLUMNS])

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    for column_cells in sheet.columns:
        max_length = max(
            len(str(cell.value or "")) for cell in column_cells
        )
        letter = column_cells[0].column_letter
        sheet.column_dimensions[letter].width = min(max(max_length + 2, 12), 55)

    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrae solicitudes de facturacion de Liverpool, guarda JSON y genera "
            "Excel con datos fiscales del detalle de cada pedido."
        )
    )
    parser.add_argument(
        "--output-dir",
        help=(
            "Carpeta de salida. Por defecto usa base_dir de settings.json o "
            "C:\\Liverpool\\auto."
        ),
    )
    parser.add_argument(
        "--edge-user-data-dir",
        help="Perfil de Edge a reutilizar. Por defecto C:\\EdgeProfiles\\LiverpoolAuto.",
    )
    parser.add_argument(
        "--fallback-driver",
        help="Ruta a msedgedriver.exe si Selenium Manager no lo detecta.",
    )
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita cuantos pedidos se visitan en detalle; util para pruebas.",
    )
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--skip-details",
        action="store_true",
        help="Solo descarga la tabla de facturas y genera archivos sin entrar al detalle.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config(args)
    service = LiverpoolService(config=config, input_callback=cli_input)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else config.base_dir / "facturacion"
    json_path = output_dir / f"facturas_{timestamp}.json"
    excel_path = output_dir / f"clientes_facturacion_{timestamp}.xlsx"

    driver = service._init_driver()

    try:
        print(f"[INFO] Abriendo {BILLS_URL}")
        driver.get(BILLS_URL)
        service._check_and_handle_login(driver)
        wait_for_bills_table(driver, config.timeout)
        set_page_size(driver, args.page_size, config.timeout)

        records = collect_all_bills(driver, config.timeout, args.max_pages)
        save_json(records, json_path)
        print(f"[INFO] JSON inicial guardado: {json_path}")

        if not args.skip_details:
            enrich_with_order_billing_data(
                driver=driver,
                service=service,
                records=records,
                timeout=config.timeout,
                limit=args.limit,
                json_path=json_path,
            )

        save_json(records, json_path)
        save_excel(records, excel_path)
        print(f"[OK] Facturas exportadas: {len(records)}")
        print(f"[OK] JSON: {json_path}")
        print(f"[OK] Excel: {excel_path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
