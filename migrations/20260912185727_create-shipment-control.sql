CREATE TABLE public.portal_orders (
  order_id text PRIMARY KEY,
  batch_date date NOT NULL,
  order_url text NOT NULL,
  created_label text NOT NULL DEFAULT '',
  liverpool_status text NOT NULL DEFAULT '',
  item_count integer NOT NULL DEFAULT 0 CHECK (item_count >= 0),
  unit_count integer NOT NULL DEFAULT 0 CHECK (unit_count >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.portal_order_items (
  order_id text NOT NULL REFERENCES public.portal_orders(order_id) ON DELETE CASCADE,
  line_number integer NOT NULL CHECK (line_number > 0),
  title text NOT NULL,
  quantity integer NOT NULL DEFAULT 1 CHECK (quantity > 0),
  offer_sku text NOT NULL DEFAULT '',
  size text NOT NULL DEFAULT '',
  PRIMARY KEY (order_id, line_number)
);

CREATE TABLE public.portal_shipments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id text NOT NULL REFERENCES public.portal_orders(order_id) ON DELETE CASCADE,
  carrier text NOT NULL CHECK (carrier IN ('ESTAFETA', 'UPS', 'DHL', 'FEDEX', 'DESCONOCIDA')),
  tracking_number text NOT NULL UNIQUE,
  tracking_url text NOT NULL,
  guide_status text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'no_movement', 'in_transit', 'out_for_delivery', 'delivered', 'exception', 'manual_review')
  ),
  status_detail text NOT NULL DEFAULT 'Pendiente de primera consulta',
  first_seen_at timestamptz NOT NULL DEFAULT now(),
  last_checked_at timestamptz,
  next_retry_at timestamptz NOT NULL DEFAULT now(),
  retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  consecutive_failures integer NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
  delivered_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.portal_tracking_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  shipment_id uuid NOT NULL REFERENCES public.portal_shipments(id) ON DELETE CASCADE,
  status text NOT NULL,
  detail text NOT NULL,
  source text NOT NULL CHECK (source IN ('liverpool', 'carrier', 'system')),
  observed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX portal_orders_batch_date_idx ON public.portal_orders (batch_date DESC);
CREATE INDEX portal_shipments_status_retry_idx ON public.portal_shipments (status, next_retry_at);
CREATE INDEX portal_shipments_order_id_idx ON public.portal_shipments (order_id);
CREATE INDEX portal_tracking_events_shipment_time_idx ON public.portal_tracking_events (shipment_id, observed_at DESC);

CREATE TRIGGER portal_orders_updated_at
BEFORE UPDATE ON public.portal_orders
FOR EACH ROW EXECUTE FUNCTION system.update_updated_at();

CREATE TRIGGER portal_shipments_updated_at
BEFORE UPDATE ON public.portal_shipments
FOR EACH ROW EXECUTE FUNCTION system.update_updated_at();

ALTER TABLE public.portal_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portal_order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portal_shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portal_tracking_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.portal_orders FROM anon, authenticated;
REVOKE ALL ON TABLE public.portal_order_items FROM anon, authenticated;
REVOKE ALL ON TABLE public.portal_shipments FROM anon, authenticated;
REVOKE ALL ON TABLE public.portal_tracking_events FROM anon, authenticated;
REVOKE ALL ON SEQUENCE public.portal_tracking_events_id_seq FROM anon, authenticated;
