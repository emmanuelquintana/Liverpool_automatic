"use client";

import { useMemo, useState } from "react";
import { ExternalLink, PackageOpen, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { OrderDTO, ShipmentStatus } from "@/lib/types";

const statusLabel: Record<ShipmentStatus | "missing", string> = {
  pending: "Pendiente",
  no_movement: "Sin movimiento",
  in_transit: "En tránsito",
  out_for_delivery: "En reparto",
  delivered: "Entregada",
  exception: "Incidencia",
  manual_review: "Revisión manual",
  missing: "Sin guía",
};

function OrderDetail({ order }: { order: OrderDTO }) {
  return (
    <Sheet>
      <SheetTrigger render={<Button variant="ghost" size="sm" />}>
        Detalle
      </SheetTrigger>
      <SheetContent className="detail-sheet sm:max-w-lg">
        <SheetHeader className="detail-header">
          <p className="eyebrow">Pedido Liverpool</p>
          <SheetTitle>#{order.order_id}</SheetTitle>
          <SheetDescription>
            {order.created_label || order.batch_date}
          </SheetDescription>
        </SheetHeader>
        <div className="detail-body">
          <section>
            <h3>Artículos</h3>
            {order.items.length ? (
              <ul className="item-list">
                {order.items.map((item) => (
                  <li key={item.line_number}>
                    <span>{item.title}</span>
                    <strong>×{item.quantity}</strong>
                    <small>
                      {[item.offer_sku, item.size].filter(Boolean).join(" · ")}
                    </small>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-copy">Sin artículos capturados.</p>
            )}
          </section>
          <section>
            <h3>Guías</h3>
            {order.shipments.length ? (
              order.shipments.map((shipment) => (
                <div className="guide-detail" key={shipment.id}>
                  <div>
                    <Badge data-status={shipment.status}>
                      {statusLabel[shipment.status]}
                    </Badge>
                    <strong>{shipment.carrier}</strong>
                  </div>
                  <code>{shipment.tracking_number}</code>
                  <p>{shipment.status_detail}</p>
                  <a
                    href={shipment.tracking_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Abrir paquetería <ExternalLink aria-hidden="true" />
                  </a>
                </div>
              ))
            ) : (
              <p className="empty-copy">
                Liverpool aún no ha entregado una guía al script.
              </p>
            )}
          </section>
        </div>
        <div className="detail-actions">
          <Button
            render={
              <a href={order.order_url} target="_blank" rel="noreferrer" />
            }
          >
            Abrir pedido en Liverpool <ExternalLink aria-hidden="true" />
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function ManifestTable({ orders }: { orders: OrderDTO[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const visible = useMemo(
    () =>
      orders.filter((order) => {
        const shipment = order.shipments[0];
        const status = shipment?.status ?? "missing";
        const haystack =
          `${order.order_id} ${shipment?.tracking_number ?? ""} ${shipment?.carrier ?? ""}`.toLowerCase();
        return (
          (filter === "all" || status === filter) &&
          haystack.includes(query.toLowerCase().trim())
        );
      }),
    [orders, query, filter],
  );
  return (
    <div className="manifest-frame">
      <div className="table-tools">
        <label className="search-field">
          <Search aria-hidden="true" />
          <span className="sr-only">Buscar pedido o guía</span>
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar pedido, guía o paquetería"
          />
        </label>
        <Select
          value={filter}
          itemToStringLabel={(value) =>
            statusLabel[value as ShipmentStatus | "missing"] ?? "Todos los estados"
          }
          onValueChange={(value) => value && setFilter(value)}
        >
          <SelectTrigger
            aria-label="Filtrar por estado"
            className="status-filter"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los estados</SelectItem>
            <SelectItem value="missing">Sin guía</SelectItem>
            <SelectItem value="no_movement">Sin movimiento</SelectItem>
            <SelectItem value="in_transit">En tránsito</SelectItem>
            <SelectItem value="delivered">Entregadas</SelectItem>
            <SelectItem value="manual_review">Revisión manual</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {!visible.length ? (
        <div className="table-empty">
          <PackageOpen aria-hidden="true" />
          <h3>No hay coincidencias</h3>
          <p>
            {orders.length
              ? "Prueba otro texto o estado."
              : "Usa “Subir al portal” en el script para enviar el primer lote."}
          </p>
        </div>
      ) : (
        <>
          <div className="desktop-table">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Pedido</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Paquetería / guía</TableHead>
                  <TableHead>Estado verificado</TableHead>
                  <TableHead>Última consulta</TableHead>
                  <TableHead className="text-right">Acción</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((order) => {
                  const shipment = order.shipments[0];
                  const status = shipment?.status ?? "missing";
                  return (
                    <TableRow
                      key={order.order_id}
                      data-attention={[
                        "no_movement",
                        "exception",
                        "manual_review",
                      ].includes(status)}
                    >
                      <TableCell>
                        <strong>#{order.order_id}</strong>
                        <small>
                          {order.unit_count} pieza
                          {order.unit_count === 1 ? "" : "s"}
                        </small>
                      </TableCell>
                      <TableCell>{order.batch_date}</TableCell>
                      <TableCell>
                        {shipment ? (
                          <>
                            <strong>{shipment.carrier}</strong>
                            <code>{shipment.tracking_number}</code>
                          </>
                        ) : (
                          <span className="muted">No capturada</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge data-status={status}>
                          {statusLabel[status]}
                        </Badge>
                        <small>{shipment?.status_detail}</small>
                      </TableCell>
                      <TableCell>
                        {shipment?.last_checked_at
                          ? new Intl.DateTimeFormat("es-MX", {
                              dateStyle: "short",
                              timeStyle: "short",
                              timeZone: "America/Mexico_City",
                            }).format(new Date(shipment.last_checked_at))
                          : "Pendiente"}
                      </TableCell>
                      <TableCell className="text-right">
                        <OrderDetail order={order} />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          <div className="mobile-manifest">
            {visible.map((order) => {
              const shipment = order.shipments[0];
              const status = shipment?.status ?? "missing";
              return (
                <article key={order.order_id}>
                  <header>
                    <div>
                      <span>Pedido</span>
                      <strong>#{order.order_id}</strong>
                    </div>
                    <Badge data-status={status}>{statusLabel[status]}</Badge>
                  </header>
                  <dl>
                    <div>
                      <dt>Fecha</dt>
                      <dd>{order.batch_date}</dd>
                    </div>
                    <div>
                      <dt>Paquetería</dt>
                      <dd>{shipment?.carrier ?? "Sin guía"}</dd>
                    </div>
                    <div>
                      <dt>Rastreo</dt>
                      <dd>{shipment?.tracking_number ?? "—"}</dd>
                    </div>
                  </dl>
                  <OrderDetail order={order} />
                </article>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
