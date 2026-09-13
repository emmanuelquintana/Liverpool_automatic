"use client";

import type { ReactNode } from "react";
import { Skeleton } from "boneyard-js/react";

export function DashboardBoundary({ children, loading = false }: { children: ReactNode; loading?: boolean }) {
  return <Skeleton name="dashboard-shell" loading={loading} animate="shimmer" stagger={45} transition={240} fallback={children}>{children}</Skeleton>;
}
