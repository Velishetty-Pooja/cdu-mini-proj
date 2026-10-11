import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'cyan' | 'amber' | 'emerald' | 'rose' | 'purple';
}

const variantStyles = {
  cyan: {
    bg: 'bg-cyan-950/30 border-cyan-800/40',
    iconBg: 'bg-cyan-500/20 text-cyan-400',
    valueColor: 'text-cyan-300',
  },
  amber: {
    bg: 'bg-amber-950/30 border-amber-800/40',
    iconBg: 'bg-amber-500/20 text-amber-400',
    valueColor: 'text-amber-300',
  },
  emerald: {
    bg: 'bg-emerald-950/30 border-emerald-800/40',
    iconBg: 'bg-emerald-500/20 text-emerald-400',
    valueColor: 'text-emerald-300',
  },
  rose: {
    bg: 'bg-rose-950/30 border-rose-800/40',
    iconBg: 'bg-rose-500/20 text-rose-400',
    valueColor: 'text-rose-300',
  },
  purple: {
    bg: 'bg-purple-950/30 border-purple-800/40',
    iconBg: 'bg-purple-500/20 text-purple-400',
    valueColor: 'text-purple-300',
  },
};

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'cyan',
}) => {
  const styles = variantStyles[variant];

  return (
    <div className={`p-4 rounded-xl border backdrop-blur-sm ${styles.bg} transition-all hover:scale-[1.01]`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg ${styles.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-2">
        <div className={`text-2xl font-extrabold ${styles.valueColor}`}>{value}</div>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};
