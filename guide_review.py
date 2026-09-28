# guide_review.py
"""
Revisión de guías con el navegador de esta máquina.

El portal no puede leer las guías de UPS: Akamai bloquea sus consultas por venir de un
datacenter y responde "Access Denied" antes de servir la página. Desde una IP normal el
sitio carga sin problema, así que la revisión se hace aquí: se abre cada guía en Edge,
se lee la barra de avance que publica la paquetería y el resultado se devuelve al portal
en el mismo archivo que lo trajo.
"""

import json
from datetime import datetime
from pathlib import Path

STATUS_LABELS = {
    "no_movement": "Sin movimiento",
    "in_transit": "En tránsito",
    "out_for_delivery": "En reparto",
    "delivered": "Entregada",
    "exception": "Incidencia",
    "manual_review": "Revisión manual",
}

VALID_STATUSES = list(STATUS_LABELS)

# UPS pinta cinco etapas fijas; la vigente trae la clase "active".
_UPS_STEPS_JS = """
const seen = new Map();
for (const el of document.querySelectorAll('.progress-step')) {
  const label = el.querySelector('.horizontalstep-aligner')?.textContent?.trim();
  if (!label) continue;
  const active = el.classList.contains('active') || !!el.closest('.progress-step.active');
  if (!seen.has(label) || active) seen.set(label, active);
}
const text = document.body ? document.body.innerText : '';
return {
  steps: [...seen].map(([label, active]) => ({label, active})),
  denied: document.title.indexOf('Access Denied') >= 0 || text.indexOf('Access Denied') >= 0,
};
"""

# Estafeta usa una clase por etapa dentro de los párrafos de la barra de avance.
_ESTAFETA_STEPS_JS = """
const steps = [];
for (const el of document.querySelectorAll('p.stateDescription')) {
  const label = (el.textContent || '').replace(/\\s+/g, ' ').trim();
  if (!label) continue;
  steps.push({label, classes: el.className.toLowerCase()});
}
const notice = document.querySelector('#i09');
return {steps, notice: notice ? notice.textContent.replace(/\\s+/g, ' ').trim() : ''};
"""

_UPS_BY_POSITION = ["no_movement", "in_transit", "in_transit", "out_for_delivery", "delivered"]

_TEXT_RULES = [
    ("no_movement", ["aun no es depositado", "no es depositado", "guia ha sido generada", "etiqueta creada", "label created"]),
    ("exception", ["excepcion", "incidencia", "no entregado", "intento de entrega", "retenido", "rezago", "devolucion", "exception", "returned"]),
    ("out_for_delivery", ["en proceso de entrega", "en ruta de entrega", "despachado para su entrega", "out for delivery", "en reparto"]),
    ("delivered", ["entregado", "entregada", "delivered"]),
    ("in_transit", ["en transito", "in transit", "en camino", "tenemos su paquete", "recibido por estafeta", "salio de"]),
]


def _normalize(text: str) -> str:
    lowered = (text or "").lower()
    for accented, plain in zip("áéíóúü", "aeiouu"):
        lowered = lowered.replace(accented, plain)
    return lowered


def _match_text(text: str):
    normalized = _normalize(text)
    for status, needles in _TEXT_RULES:
        if any(needle in normalized for needle in needles):
            return status
    return ""


def classify_ups(steps) -> tuple:
    """Devuelve (estado, detalle) a partir de la barra de avance de UPS."""
    current = next((index for index, step in enumerate(steps) if step.get("active")), -1)
    if current < 0:
        return "", ""
    label = steps[current].get("label", "")
    status = _match_text(label)
    if not status and len(steps) == len(_UPS_BY_POSITION):
        status = _UPS_BY_POSITION[current]
    return status, f"UPS: {label}" if status else ""


def classify_estafeta(steps, notice: str = "") -> tuple:
    """Devuelve (estado, detalle) a partir de la barra de avance de Estafeta."""
    parsed = [(step.get("classes", ""), step.get("label", "")) for step in steps if step.get("label")]
    final = next((label for classes, label in parsed if "entregad" in _normalize(label)), "")
    final_classes = next((classes for classes, label in parsed if label == final), "")
    if final and ("fontcolorcurrentprocess" in final_classes.split() or "fontcolorprocessed" in final_classes.split()):
        return "delivered", "Estafeta: Entregado"
    failed = next((label for classes, label in parsed if "fontcolorerror" in classes.split()), "")
    if failed:
        return "exception", f'Estafeta: incidencia en "{failed}"'
    current = next((label for classes, label in reversed(parsed) if "fontcolorcurrentprocess" in classes.split()), "")
    if current:
        status = _match_text(current)
        return (status, f"Estafeta: {current}") if status else ("", "")
    if notice:
        status = _match_text(notice)
        if status:
            return status, notice[:300]
    if parsed and all("fontcolorpending" in classes.split() for classes, _ in parsed):
        return "no_movement", "Estafeta: la guía aún no se deposita"
    return "", ""


def load_guides(path) -> tuple:
    """Lee el archivo que entrega el portal. Devuelve (documento, guías)."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    guides = document.get("guias")
    if not isinstance(guides, list) or not guides:
        raise ValueError("El archivo no trae la lista de guías del portal.")
    return document, guides


def save_guides(path, document, guides):
    """Escribe el archivo revisado conservando todo lo que trajo el portal."""
    document = dict(document)
    document["guias"] = guides
    document["revisado_en"] = datetime.now().astimezone().isoformat(timespec="seconds")
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def review_guide(driver, guide: dict, wait_seconds: int = 25) -> tuple:
    """Abre una guía en el navegador y devuelve (estado, detalle)."""
    import time

    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    carrier = (guide.get("carrier") or "").upper()
    tracking_number = guide.get("tracking_number", "")
    url = guide.get("tracking_url") or ""
    if not url:
        if carrier == "UPS":
            url = f"https://www.ups.com/track?loc=es_MX&tracknum={tracking_number}&requester=ST"
        elif carrier == "ESTAFETA":
            url = f"https://cs.estafeta.com/es/Tracking/searchByGet?wayBill={tracking_number}&isShipmentDetail=True"
        else:
            return "", "Sin liga de rastreo"

    driver.get(url)
    selector = ".progress-step .horizontalstep-aligner" if carrier == "UPS" else "p.stateDescription"
    try:
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException:
        pass
    time.sleep(1)  # la barra termina de pintarse un instante después de aparecer

    if carrier == "UPS":
        data = driver.execute_script(_UPS_STEPS_JS) or {}
        if data.get("denied"):
            return "", "UPS bloqueó la consulta desde esta red"
        status, detail = classify_ups(data.get("steps") or [])
        if not status:
            return "", "No se encontró la barra de avance de UPS"
        return status, detail

    data = driver.execute_script(_ESTAFETA_STEPS_JS) or {}
    status, detail = classify_estafeta(data.get("steps") or [], data.get("notice", ""))
    if not status:
        return "", "No se encontró la barra de avance de la paquetería"
    return status, detail
