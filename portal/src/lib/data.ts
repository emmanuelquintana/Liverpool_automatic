"use server";

import "server-only";
import { createAdminClient } from "@insforge/sdk";
import { revalidatePath } from "next/cache";
import type { OrderDTO } from "@/lib/types";

const baseUrl =
  process.env.INSFORGE_URL ?? "https://hbfjb9ga.us-east.insforge.app";
const client = () =>
  createAdminClient({ baseUrl, apiKey: process.env.INSFORGE_API_KEY! });

export async function getDashboardData(): Promise<{
  orders: OrderDTO[];
  error?: string;
}> {
  if (!process.env.INSFORGE_API_KEY)
    return { orders: [], error: "Falta INSFORGE_API_KEY en Vercel" };
  const { data, error } = await client()
    .database.from("portal_orders")
    .select(
      "order_id,batch_date,order_url,created_label,liverpool_status,item_count,unit_count,portal_order_items(line_number,title,quantity,offer_sku,size),portal_shipments(id,carrier,tracking_number,tracking_url,guide_status,status,status_detail,first_seen_at,last_checked_at,consecutive_failures)",
    )
    .order("batch_date", { ascending: false })
    .limit(250);
  if (error) return { orders: [], error: error.message };
  return {
    orders: (data ?? []).map((row: Record<string, unknown>) => ({
      ...row,
      items: row.portal_order_items ?? [],
      shipments: row.portal_shipments ?? [],
    })) as OrderDTO[],
  };
}

export async function refreshTracking() {
  if (!process.env.PORTAL_TOKEN) return;
  await fetch(`${baseUrl}/functions/shipment-control`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-portal-token": process.env.PORTAL_TOKEN,
    },
    body: JSON.stringify({ action: "track_due", refresh_all: true }),
    cache: "no-store",
  });
  revalidatePath("/");
}
