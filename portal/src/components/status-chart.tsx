"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

const config = {
  total: { label: "Guías", color: "var(--signal-blue)" },
} satisfies ChartConfig;

export function StatusChart({
  data,
}: {
  data: { status: string; name: string; total: number }[];
}) {
  if (!data.length)
    return (
      <div className="chart-empty">
        Las guías aparecerán aquí después de la primera carga desde el script.
      </div>
    );
  return (
    <ChartContainer
      config={config}
      className="status-chart"
      initialDimension={{ width: 620, height: 260 }}
    >
      <BarChart
        accessibilityLayer
        data={data}
        margin={{ left: 0, right: 12, top: 8 }}
      >
        <CartesianGrid vertical={false} strokeDasharray="3 6" />
        <XAxis
          dataKey="name"
          tickLine={false}
          axisLine={false}
          tickMargin={10}
        />
        <YAxis
          allowDecimals={false}
          tickLine={false}
          axisLine={false}
          width={24}
        />
        <ChartTooltip
          cursor={{ fill: "var(--muted)" }}
          content={<ChartTooltipContent hideLabel />}
        />
        <Bar dataKey="total" fill="var(--color-total)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  );
}
