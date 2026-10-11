import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { ClassCount } from '../types';

interface VehicleCountsChartProps {
  classCounts: ClassCount[];
}

const CLASS_PALETTE: Record<string, string> = {
  Car: '#38bdf8',          // Sky Blue
  Motorcycle: '#fbbf24',   // Amber
  Bus: '#c084fc',          // Purple
  Truck: '#fb923c',        // Orange
  Bicycle: '#22d3ee',      // Cyan
  Pedestrian: '#4ade80',   // Emerald Green
  'Auto-rickshaw': '#f59e0b',
};

export const VehicleCountsChart: React.FC<VehicleCountsChartProps> = ({ classCounts }) => {
  if (!classCounts || classCounts.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
        No road user detections to display.
      </div>
    );
  }

  const chartData = classCounts.map((c) => ({
    name: c.class_name,
    count: c.count,
    percentage: c.percentage,
    color: CLASS_PALETTE[c.class_name] || '#94a3b8',
  }));

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <XAxis
            dataKey="name"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            interval={0}
            angle={-15}
            textAnchor="end"
          />
          <YAxis stroke="#64748b" fontSize={11} tickLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#f8fafc',
            }}
            formatter={(value: any, name: any, props: any) => [
              `${value} (${props.payload.percentage}%)`,
              'Detections',
            ]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
