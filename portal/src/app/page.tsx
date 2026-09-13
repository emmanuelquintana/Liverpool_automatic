import { Suspense } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  Clock3,
  PackageSearch,
  RefreshCw,
  Route,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ManifestTable } from "@/components/manifest-table";
import { StatusChart } from "@/components/status-chart";
import { getDashboardData, refreshTracking } from "@/lib/data";

export const dynamic = "force-dynamic";

const label: Record<string, string> = {
  pending: "Pendiente",
  no_movement: "Sin movimiento",
  in_transit: "En tránsito",
  out_for_delivery: "En reparto",
  delivered: "Entregada",
  exception: "Incidencia",
  manual_review: "Revisión manual",
};

async function Dashboard() {
  const { orders, error } = await getDashboardData();
  const shipments = orders.flatMap((order) => order.shipments);
  const count = (status: string) =>
    shipments.filter((shipment) => shipment.status === status).length;
  const attention = shipments.filter((shipment) =>
    ["no_movement", "exception", "manual_review"].includes(shipment.status),
  );
  const withoutGuide = orders.filter(
    (order) => order.shipments.length === 0,
  ).length;
  const lastCheck = shipments
    .map((shipment) => shipment.last_checked_at)
    .filter(Boolean)
    .sort()
    .at(-1);
  const chart = Object.keys(label)
    .map((status) => ({ status, name: label[status], total: count(status) }))
    .filter((item) => item.total);

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Navegación principal">
        <a
          className="brand"
          href="#inicio"
          aria-label="Liverpool Seguimiento Goldval, inicio"
        >
          <span className="brand-mark" aria-hidden="true">
            G
          </span>
          <span>
            <strong>Liverpool</strong>
            <small>Seguimiento · Goldval</small>
          </span>
        </a>
        <nav>
          <a className="nav-link is-active" href="#inicio">
            <Route aria-hidden="true" /> Operación
          </a>
          <a className="nav-link" href="#manifiesto">
            <Boxes aria-hidden="true" /> Pedidos
          </a>
          <a className="nav-link" href="#seguimiento">
            <PackageSearch aria-hidden="true" /> Seguimiento
          </a>
        </nav>
        <div className="sidebar-foot">
          <span className="live-dot" aria-hidden="true" />
          <span>
            <strong>Monitoreo activo</strong>
            <small>Próximo ciclo cada 15 min</small>
          </span>
        </div>
      </aside>

      <main id="inicio" className="main-canvas">
        <header className="topbar">
          <div>
            <p className="eyebrow">Centro de operaciones</p>
            <h1>Control de envíos</h1>
          </div>
          <form action={refreshTracking}>
            <Button type="submit" className="refresh-button">
              <RefreshCw aria-hidden="true" /> Actualizar ahora
            </Button>
          </form>
        </header>

        <section
          className={`risk-band ${attention.length ? "has-risk" : "is-clear"}`}
          aria-labelledby="risk-title"
        >
          <div className="risk-icon">
            <AlertTriangle aria-hidden="true" />
          </div>
          <div>
            <p className="eyebrow">Prioridad de hoy</p>
            <h2 id="risk-title">
              {attention.length
                ? `${attention.length} guía${attention.length === 1 ? "" : "s"} requieren revisión`
                : "No hay guías con alerta"}
            </h2>
            <p>
              {attention.length
                ? "UPS, DHL y FedEx pueden bloquear la lectura automática; el último estado confiable siempre se conserva."
                : "El servidor no detecta incidencias ni guías detenidas en este momento."}
            </p>
          </div>
          <a href="#manifiesto">
            Ver manifiesto <ArrowUpRight aria-hidden="true" />
          </a>
        </section>

        {error && (
          <div className="data-warning" role="status">
            Backend conectado, pero la lectura falló: {error}
          </div>
        )}

        <section className="metric-strip" aria-label="Resumen de guías">
          <div>
            <span>Guías activas</span>
            <strong>{shipments.length - count("delivered")}</strong>
            <small>{shipments.length} registradas</small>
          </div>
          <div>
            <span>Sin movimiento</span>
            <strong className="amber">{count("no_movement")}</strong>
            <small>requieren vigilancia</small>
          </div>
          <div>
            <span>En ruta</span>
            <strong className="blue">
              {count("in_transit") + count("out_for_delivery")}
            </strong>
            <small>tránsito + reparto</small>
          </div>
          <div>
            <span>Entregadas</span>
            <strong className="green">{count("delivered")}</strong>
            <small>cierre confirmado</small>
          </div>
        </section>

        <section id="seguimiento" className="overview-grid">
          <div className="chart-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Distribución actual</p>
                <h2>Estado de las guías</h2>
              </div>
              <span>{shipments.length} totales</span>
            </div>
            <StatusChart data={chart} />
          </div>
          <div className="pulse-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Pulso del sistema</p>
                <h2>Salud operativa</h2>
              </div>
              <Clock3 aria-hidden="true" />
            </div>
            <dl>
              <div>
                <dt>Última consulta</dt>
                <dd>
                  {lastCheck
                    ? new Intl.DateTimeFormat("es-MX", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "America/Mexico_City",
                      }).format(new Date(lastCheck))
                    : "Aún sin consultas"}
                </dd>
              </div>
              <div>
                <dt>Pedidos sin guía capturada</dt>
                <dd>{withoutGuide}</dd>
              </div>
              <div>
                <dt>Actualización completa</dt>
                <dd>Diario · 06:00</dd>
              </div>
              <div>
                <dt>Reintentos</dt>
                <dd>5 min → 30 min → 2 h → 6 h</dd>
              </div>
            </dl>
            <p className="truth-note">
              <CheckCircle2 aria-hidden="true" /> Nunca se sustituye un estado
              conocido por una suposición.
            </p>
          </div>
        </section>

        <section id="manifiesto" className="manifest-section">
          <div className="section-heading manifest-heading">
            <div>
              <p className="eyebrow">Manifiesto operativo</p>
              <h2>Pedidos y seguimiento</h2>
            </div>
            <span>{orders.length} pedidos</span>
          </div>
          <ManifestTable orders={orders} />
        </section>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={null}>
      <Dashboard />
    </Suspense>
  );
}
