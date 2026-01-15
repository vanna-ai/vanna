import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

const backgroundData = [
  { month: "Jan", value: 2100000 },
  { month: "Feb", value: 2250000 },
  { month: "Mar", value: 2400000 },
  { month: "Apr", value: 2350000 },
  { month: "May", value: 2600000 },
  { month: "Jun", value: 2750000 },
  { month: "Jul", value: 2900000 },
  { month: "Aug", value: 2850000 },
  { month: "Sep", value: 3100000 },
  { month: "Oct", value: 3250000 },
  { month: "Nov", value: 3400000 },
  { month: "Dec", value: 3200000 },
];

export function AnimatedChartBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden opacity-[0.03] pointer-events-none">
      <div className="w-full h-full scale-110 animate-pulse" style={{ animationDuration: '8s' }}>
        <AreaChart
          width={2000}
          height={1000}
          data={backgroundData}
          margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="bgGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.8} />
              <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
          <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
          <YAxis stroke="hsl(var(--muted-foreground))" />
          <Area
            type="monotone"
            dataKey="value"
            stroke="hsl(217, 91%, 60%)"
            fill="url(#bgGradient)"
            strokeWidth={2}
          />
        </AreaChart>
      </div>
    </div>
  );
}
