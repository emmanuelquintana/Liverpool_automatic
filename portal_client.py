import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PORTAL_URL = "https://hbfjb9ga.us-east.insforge.app/functions/shipment-control"


def build_payload(days, selected_dates):
    return {"days": [days[date].to_dict() for date in selected_dates if date in days]}


def upload_batches(days, selected_dates):
    token = os.environ.get("KODAURA_PORTAL_TOKEN", "")
    if not token:
        raise RuntimeError("Falta KODAURA_PORTAL_TOKEN. Reinicia la aplicación después de instalar el portal.")
    payload = build_payload(days, selected_dates)
    if not payload["days"]:
        raise RuntimeError("Las fechas seleccionadas no contienen pedidos.")
    request = Request(
        os.environ.get("KODAURA_PORTAL_URL", DEFAULT_PORTAL_URL),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-portal-token": token},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"El portal rechazó la carga ({error.code}): {detail[:300]}") from error
    except URLError as error:
        raise RuntimeError(f"No se pudo conectar con el portal: {error.reason}") from error
