import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface TimeSeriesChartProps {
  timeline: Array<{
    frame: number;
    timestamp: number;
    vehicles: number;
    pedestrians: number;
    congestion_occupancy: number;
    congestion_level: string;
  }>;
}

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ timeline }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-xs">
        Timeline metrics are available for processed video streams.
      </div>
    );
  }

  const chartData = timeline.map((t) => ({
    time: `${t.timestamp.toFixed(1)}s`,
    Vehicles: t.vehicles,
    Pedestrians: t.pedestrians,
    'Occupancy %': Math.round(t.congestion_occupancy * 100),
  }));

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
          <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} />
          <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '8px',
              fontSize: '11px',
              color: '#f8fafc',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
          <Line type="monotone" dataKey="Vehicles" stroke="#38bdf8" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Occupancy %" stroke="#fbbf24" strokeWidth={1.5} dot={false} />
          <Line type="monotone" dataKey="Pedestrians" stroke="#4ade80" strokeWidth={1.5} dot={false} strokeDasharray="3 3" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
