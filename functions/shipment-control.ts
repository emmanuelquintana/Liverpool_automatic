export type TrackingStatus =
  | "no_movement"
  | "in_transit"
  | "out_for_delivery"
  | "delivered"
  | "exception"
  | "manual_review";

const visibleText = (html: string) => html
  .replace(/<script[\s\S]*?<\/script>/gi, " ")
  .replace(/<style[\s\S]*?<\/style>/gi, " ")
  .replace(/<[^>]+>/g, " ")
  .replace(/&nbsp;|&#160;/gi, " ")
  .replace(/&aacute;/gi, "a").replace(/&eacute;/gi, "e").replace(/&iacute;/gi, "i")
  .replace(/&oacute;/gi, "o").replace(/&uacute;/gi, "u")
  .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  .replace(/\s+/g, " ").toLowerCase();

export function classifyTrackingHtml(html: string, carrier = "ESTAFETA", trackingNumber = ""): { status: TrackingStatus; detail: string } {
  let evidence = "";
  if (carrier === "ESTAFETA") {
    evidence = html.match(/<[^>]*class=["'][^"']*fontColorCurrentProcess[^"']*["'][^>]*>([\s\S]{0,1200}?)<\//i)?.[1] ?? "";
  } else if (trackingNumber && html.toUpperCase().includes(trackingNumber.toUpperCase())) {
    evidence = [...html.matchAll(/["'](?:statusDescription|status_description|checkpoint_status)["']\s*:\s*["']([^"']{2,180})["']/gi)].map((match) => match[1]).join(" ");
  }
  if (!evidence) return { status: "manual_review", detail: "La página respondió, pero no expuso un estado verificable" };
  const body = visibleText(evidence);
  const has = (needles: string[]) => needles.some((needle) => body.includes(needle));
  if (has(["entregado", "delivered", "recibido por"])) return { status: "delivered", detail: "La paquetería reporta el envío como entregado" };
  if (has(["en ruta de entrega", "en camino para entrega", "out for delivery"])) return { status: "out_for_delivery", detail: "El paquete está en ruta de entrega" };
  if (has(["excepcion", "delivery attempted", "intento de entrega", "retenido", "returning to sender"])) return { status: "exception", detail: "La paquetería reporta una incidencia" };
  if (has(["en transito", "in transit", "on the way", "salio de", "llego a las instalaciones"])) return { status: "in_transit", detail: "El paquete está en tránsito" };
  if (has(["aun no es depositado", "guia ha sido generada", "label created", "shipment ready for ups", "informacion de envio enviada"])) return { status: "no_movement", detail: "Guía creada; la paquetería aún no registra movimiento" };
  return { status: "manual_review", detail: "La página respondió, pero no expuso un estado verificable" };
}

export function carrierName(value: string): "ESTAFETA" | "UPS" | "DHL" | "FEDEX" | "DESCONOCIDA" {
  const normalized = value.toUpperCase();
  if (normalized.includes("ESTAFETA")) return "ESTAFETA";
  if (normalized.includes("UPS") || /\b1Z[A-Z0-9]{16}\b/.test(normalized)) return "UPS";
  if (normalized.includes("DHL")) return "DHL";
  if (normalized.includes("FEDEX") || normalized.includes("FEDERAL EXPRESS")) return "FEDEX";
  return "DESCONOCIDA";
}

export function trackingUrl(carrier: ReturnType<typeof carrierName>, guide: string): string {
  const value = encodeURIComponent(guide);
  if (carrier === "ESTAFETA") return `https://cs.estafeta.com/es/Tracking/searchByGet?wayBill=${value}&isShipmentDetail=True`;
  if (carrier === "UPS") return `https://www.ups.com/track?loc=es_MX&tracknum=${value}`;
  if (carrier === "DHL") return `https://www.dhl.com/mx-es/home/rastreo.html?tracking-id=${value}&submit=1`;
  if (carrier === "FEDEX") return `https://www.fedex.com/apps/fedextrack/?tracknumbers=${value}&locale=es_MX&cntry_code=mx`;
  return "";
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8" } });

const admin = async () => {
  const { createAdminClient } = await import("npm:@insforge/sdk");
  return createAdminClient({ baseUrl: Deno.env.get("INSFORGE_BASE_URL")!, apiKey: Deno.env.get("API_KEY")! });
};

function authorized(req: Request) {
  const supplied = req.headers.get("x-portal-token") ?? req.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  return Boolean(supplied && supplied === Deno.env.get("PORTAL_TOKEN"));
}

const clean = (value: unknown, max = 500) => String(value ?? "").trim().slice(0, max);

function batchesFrom(payload: Record<string, unknown>) {
  if (Array.isArray(payload.days)) return payload.days as Record<string, unknown>[];
  if (Array.isArray(payload.orders)) return [payload];
  return Object.values(payload).filter((entry) => entry && typeof entry === "object" && Array.isArray((entry as Record<string, unknown>).orders)) as Record<string, unknown>[];
}

async function ingest(payload: Record<string, unknown>) {
  const db = (await admin()).database;
  const batches = batchesFrom(payload);
  const orders = batches.flatMap((batch) => {
    const date = clean(batch.date, 10);
    return (batch.orders as Record<string, unknown>[]).map((order) => ({ date, order }));
  });
  if (!orders.length || orders.length > 1000) throw new Error("El lote debe contener entre 1 y 1000 pedidos");

  let shipmentCount = 0;
  for (const { date, order } of orders) {
    const orderId = clean(order.order_id, 80);
    const orderUrl = clean(order.url, 1000);
    if (!orderId || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^https:\/\//.test(orderUrl)) {
      throw new Error(`Pedido inválido: ${orderId || "sin identificador"}`);
    }
    const items = Array.isArray(order.items) ? order.items as Record<string, unknown>[] : [];
    const orderRow = {
      order_id: orderId,
      batch_date: date,
      order_url: orderUrl,
      created_label: clean(order.fecha_texto, 80),
      liverpool_status: clean(order.estado, 120),
      item_count: items.length,
      unit_count: items.reduce((sum, item) => sum + Math.max(1, Number(item.qty) || 1), 0),
    };
    const { error: orderError } = await db.from("portal_orders").upsert(orderRow, { onConflict: "order_id" });
    if (orderError) throw orderError;

    if (items.length) {
      const rows = items.map((item, index) => ({
        order_id: orderId,
        line_number: index + 1,
        title: clean(item.title, 500),
        quantity: Math.max(1, Number(item.qty) || 1),
        offer_sku: clean(item.sku_oferta, 120),
        size: clean(item.talla, 80),
      }));
      const { error } = await db.from("portal_order_items").upsert(rows, { onConflict: "order_id,line_number" });
      if (error) throw error;
    }

    const incomingShipments = Array.isArray(order.shipments)
      ? order.shipments as Record<string, unknown>[]
      : [order];
    for (const incoming of incomingShipments) {
      const trackingNumber = clean(incoming.tracking_number ?? incoming.numero_rastreo ?? incoming.guia, 120);
      if (!trackingNumber) continue;
      const source = [incoming.carrier, incoming.transportista, incoming.tracking_url, trackingNumber].map(String).join(" ");
      const carrier = carrierName(source);
      const sourceUrl = clean(incoming.tracking_url, 1200);
      const url = /^https:\/\//.test(sourceUrl) ? sourceUrl : trackingUrl(carrier, trackingNumber);
      if (!url) continue;

      const { data: previous, error: readError } = await db.from("portal_shipments")
        .select("id, guide_status")
        .eq("tracking_number", trackingNumber)
        .maybeSingle();
      if (readError) throw readError;
      const guideStatus = clean(incoming.guide_status ?? incoming.estado_guia, 160);
      const { data: shipment, error: shipmentError } = await db.from("portal_shipments").upsert({
        order_id: orderId,
        carrier,
        tracking_number: trackingNumber,
        tracking_url: url,
        guide_status: guideStatus,
        ...(previous ? {} : { status: "pending", status_detail: "Pendiente de primera consulta", next_retry_at: new Date().toISOString() }),
      }, { onConflict: "tracking_number" }).select("id").single();
      if (shipmentError) throw shipmentError;
      shipmentCount++;

      if (!previous || previous.guide_status !== guideStatus) {
        const { error } = await db.from("portal_tracking_events").insert([{
          shipment_id: shipment.id,
          status: "pending",
          detail: guideStatus || "Guía recibida desde Liverpool",
          source: "liverpool",
        }]);
        if (error) throw error;
      }
    }
  }
  return { imported_orders: orders.length, imported_shipments: shipmentCount };
}

function retryAt(failures: number, status: string) {
  if (status === "no_movement") return new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();
  const waits = [5, 30, 120, 360];
  return new Date(Date.now() + waits[Math.min(failures, waits.length - 1)] * 60 * 1000).toISOString();
}

async function checkShipment(shipment: Record<string, unknown>) {
  const db = (await admin()).database;
  const now = new Date().toISOString();
  try {
    const response = await fetch(String(shipment.tracking_url), {
      redirect: "follow",
      headers: { "user-agent": "Mozilla/5.0 (compatible; GoldvalShipmentMonitor/1.0)" },
      signal: AbortSignal.timeout(18_000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const parsed = classifyTrackingHtml(html.slice(0, 2_000_000), String(shipment.carrier), String(shipment.tracking_number));
    const failures = parsed.status === "manual_review" ? Number(shipment.consecutive_failures) + 1 : 0;
    const changed = shipment.status !== parsed.status || shipment.status_detail !== parsed.detail;
    const { error } = await db.from("portal_shipments").update({
      status: parsed.status,
      status_detail: parsed.detail,
      last_checked_at: now,
      next_retry_at: retryAt(failures, parsed.status),
      retry_count: Number(shipment.retry_count) + 1,
      consecutive_failures: failures,
      ...(parsed.status === "delivered" && !shipment.delivered_at ? { delivered_at: now } : {}),
    }).eq("id", shipment.id);
    if (error) throw error;
    if (changed) await db.from("portal_tracking_events").insert([{
      shipment_id: shipment.id,
      status: parsed.status,
      detail: parsed.detail,
      source: "carrier",
    }]);
    return parsed.status;
  } catch (error) {
    const failures = Number(shipment.consecutive_failures) + 1;
    const detail = `Consulta fallida: ${error instanceof Error ? error.message : "error desconocido"}`.slice(0, 500);
    await db.from("portal_shipments").update({
      status: "manual_review",
      status_detail: detail,
      last_checked_at: now,
      next_retry_at: retryAt(failures, "manual_review"),
      retry_count: Number(shipment.retry_count) + 1,
      consecutive_failures: failures,
    }).eq("id", shipment.id);
    return "manual_review";
  }
}

async function trackDue(refreshAll = false) {
  const db = (await admin()).database;
  if (refreshAll) {
    const { error } = await db.from("portal_shipments").update({ next_retry_at: new Date().toISOString() }).neq("status", "delivered");
    if (error) throw error;
  }
  const { data, error } = await db.from("portal_shipments")
    .select("id, carrier, tracking_number, tracking_url, status, status_detail, retry_count, consecutive_failures, delivered_at")
    .neq("status", "delivered")
    .lte("next_retry_at", new Date().toISOString())
    .order("next_retry_at", { ascending: true })
    .limit(24);
  if (error) throw error;
  const rows = data ?? [];
  const results: string[] = [];
  for (let index = 0; index < rows.length; index += 3) {
    results.push(...await Promise.all(rows.slice(index, index + 3).map(checkShipment)));
  }
  return { checked: rows.length, statuses: results.reduce<Record<string, number>>((acc, status) => ({ ...acc, [status]: (acc[status] ?? 0) + 1 }), {}) };
}

export default async function handler(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204 });
  if (req.method !== "POST") return json({ error: "Método no permitido" }, 405);
  if (!authorized(req)) return json({ error: "No autorizado" }, 401);
  try {
    const body = await req.json() as Record<string, unknown>;
    const action = clean(body.action, 40) || "ingest";
    return json(action === "track_due" ? await trackDue(Boolean(body.refresh_all)) : await ingest(body));
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : "Error interno" }, 400);
  }
}
