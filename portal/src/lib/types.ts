export type ShipmentStatus =
  | "pending"
  | "no_movement"
  | "in_transit"
  | "out_for_delivery"
  | "delivered"
  | "exception"
  | "manual_review";

export type ShipmentDTO = {
  id: string;
  carrier: string;
  tracking_number: string;
  tracking_url: string;
  guide_status: string;
  status: ShipmentStatus;
  status_detail: string;
  first_seen_at: string;
  last_checked_at: string | null;
  consecutive_failures: number;
};

export type OrderDTO = {
  order_id: string;
  batch_date: string;
  order_url: string;
  created_label: string;
  liverpool_status: string;
  item_count: number;
  unit_count: number;
  items: {
    line_number: number;
    title: string;
    quantity: number;
    offer_sku: string;
    size: string;
  }[];
  shipments: ShipmentDTO[];
};
