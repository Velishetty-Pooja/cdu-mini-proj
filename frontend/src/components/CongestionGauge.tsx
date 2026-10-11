import React from 'react';
import { Gauge, Info } from 'lucide-react';
import { CongestionMetrics } from '../types';

interface CongestionGaugeProps {
  congestion: CongestionMetrics;
}

export const CongestionGauge: React.FC<CongestionGaugeProps> = ({ congestion }) => {
  const percentage = Math.min(100, Math.round(congestion.occupancy_ratio * 100));

  const levelColors: Record<string, { bar: string; badge: string; textColor: string }> = {
    Low: {
      bar: 'bg-emerald-500',
      badge: 'bg-emerald-950/60 text-emerald-300 border-emerald-800',
      textColor: 'text-emerald-400',
    },
    Moderate: {
      bar: 'bg-amber-500',
      badge: 'bg-amber-950/60 text-amber-300 border-amber-800',
      textColor: 'text-amber-400',
    },
    High: {
      bar: 'bg-rose-500',
      badge: 'bg-rose-950/60 text-rose-300 border-rose-800',
      textColor: 'text-rose-400',
    },
  };
  const activeStyle = levelColors[congestion.level] || {
    bar: 'bg-cyan-500',
    badge: 'bg-cyan-950/60 text-cyan-300 border-cyan-800',
    textColor: 'text-cyan-400',
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Gauge className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Congestion & Roadway Occupancy
          </span>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${activeStyle.badge}`}>
          {congestion.level}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Road Space Utilisation</span>
          <span className="font-bold text-white">{percentage}%</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden p-0.5 border border-slate-700/50">
          <div
            className={`h-full rounded-full transition-all duration-500 ${activeStyle.bar}`}
            style={{ width: `${Math.max(4, percentage)}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-slate-500 pt-0.5">
          <span>0% (Free Flow)</span>
          <span>20% (Moderate)</span>
          <span>45%+ (Heavy Congestion)</span>
        </div>
      </div>

      {/* Explanation */}
      <p className="text-xs text-slate-300 mt-3 leading-relaxed">
        {congestion.description}
      </p>

      {/* Methodology disclaimer */}
      <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-start space-x-1.5 text-[11px] text-slate-400">
        <Info className="w-3.5 h-3.5 text-cyan-500 shrink-0 mt-0.5" />
        <span className="leading-tight">
          {congestion.methodology_note}
        </span>
      </div>
    </div>
  );
};
