import json
import tempfile
from pathlib import Path

from guide_review import classify_estafeta, classify_ups, load_guides, save_guides


# ── UPS: cinco etapas fijas, la vigente viene marcada como activa ──────────
def ups(active):
    labels = ["Etiqueta creada", "Tenemos su paquete", "En camino", "Despachado para su entrega", "Entrega"]
    return [{"label": label, "active": label == active} for label in labels]


assert classify_ups(ups("Etiqueta creada")) == ("no_movement", "UPS: Etiqueta creada")
assert classify_ups(ups("Tenemos su paquete"))[0] == "in_transit"
assert classify_ups(ups("En camino"))[0] == "in_transit"
assert classify_ups(ups("Despachado para su entrega"))[0] == "out_for_delivery"
# "Entrega" no cae en ninguna regla de texto: la resuelve su posición final.
assert classify_ups(ups("Entrega"))[0] == "delivered"
assert classify_ups(ups("ninguna")) == ("", "")
assert classify_ups([]) == ("", "")


# ── Estafeta: una clase por etapa dentro de la barra de avance ─────────────
def estafeta(states):
    labels = ["Recibido por Estafeta", "En Tránsito", "En Proceso de Entrega a Domicilio", "Entregado"]
    return [{"label": label, "classes": f"statedescription {state}"} for label, state in zip(labels, states)]


processed, current, pending, error = "fontcolorprocessed", "fontcolorcurrentprocess", "fontcolorpending", "fontcolorerror"

assert classify_estafeta(estafeta([current, pending, pending, pending]))[0] == "in_transit"
assert classify_estafeta(estafeta([processed, current, pending, pending]))[0] == "in_transit"
assert classify_estafeta(estafeta([processed, processed, current, pending]))[0] == "out_for_delivery"
assert classify_estafeta(estafeta([processed, processed, processed, current]))[0] == "delivered"
assert classify_estafeta(estafeta([processed, error, pending, pending]))[0] == "exception"
assert classify_estafeta(estafeta([pending, pending, pending, pending]))[0] == "no_movement"
assert classify_estafeta([], "La guía ha sido generada sin embargo el envío aún no es depositado")[0] == "no_movement"


# ── El archivo del portal viaja de ida y vuelta sin perder nada ────────────
document = {
    "generado_en": "2026-09-28T10:00:00.000Z",
    "portal": "liverpool-seguimiento-goldval",
    "guias": [{"tracking_number": "1Z6751V50428845352", "carrier": "UPS", "estado_revisado": "", "detalle_revisado": ""}],
}

with tempfile.TemporaryDirectory() as folder:
    source = Path(folder) / "pendientes.json"
    source.write_text(json.dumps(document), encoding="utf-8")
    loaded_document, guides = load_guides(source)
    assert guides[0]["tracking_number"] == "1Z6751V50428845352"

    status, detail = classify_ups(ups("Etiqueta creada"))
    guides[0]["estado_revisado"] = status
    guides[0]["detalle_revisado"] = detail

    target = Path(folder) / "revisadas.json"
    save_guides(target, loaded_document, guides)
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written["guias"][0]["estado_revisado"] == "no_movement"
    assert written["portal"] == "liverpool-seguimiento-goldval"
    assert written["revisado_en"]

try:
    load_guides.__call__
    with tempfile.TemporaryDirectory() as folder:
        empty = Path(folder) / "vacio.json"
        empty.write_text(json.dumps({"guias": []}), encoding="utf-8")
        load_guides(empty)
    raise AssertionError("un archivo sin guías debe fallar")
except ValueError:
    pass

print("guide review: ok")
