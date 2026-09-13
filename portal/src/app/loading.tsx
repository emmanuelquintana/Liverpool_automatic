import { DashboardBoundary } from "@/components/dashboard-boundary";

export default function Loading() {
  return <DashboardBoundary loading><div className="loading-blueprint"><aside /><main><header /><section className="loading-risk" /><section className="loading-metrics" /><section className="loading-grid" /><section className="loading-table" /></main></div></DashboardBoundary>;
}
