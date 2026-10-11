import React from 'react';
import {
  Activity,
  Upload,
  BarChart3,
  AlertTriangle,
  History,
  Settings,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';
import { HealthResponse } from '../types';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  health: HealthResponse | null;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onTabChange, health }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'upload', label: 'Upload & Analyse', icon: Upload },
    { id: 'details', label: 'Analysis Details', icon: BarChart3 },
    { id: 'events', label: 'Traffic Events', icon: AlertTriangle },
    { id: 'history', label: 'Analysis History', icon: History },
    { id: 'settings', label: 'Reports & Settings', icon: Settings },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange('dashboard')}>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-cyan-600 to-amber-500 flex items-center justify-center shadow-md">
              <span className="text-white font-extrabold text-lg tracking-wider">ITI</span>
            </div>
            <div>
              <div className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                Indian Traffic Intelligence
                <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-cyan-900/60 text-cyan-300 border border-cyan-700/50">
                  v2.0
                </span>
              </div>
              <p className="text-xs text-slate-400">Computer Vision & Trajectory Analysis</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Health & Engine Status */}
          <div className="flex items-center space-x-3">
            {health?.ready ? (
              <div className="flex items-center space-x-2 bg-emerald-950/60 border border-emerald-800/60 px-2.5 py-1 rounded-full text-xs text-emerald-300">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-medium hidden sm:inline">{health.model_name} ({health.device.toUpperCase()})</span>
                <span className="font-medium sm:hidden">Online</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 bg-rose-950/60 border border-rose-800/60 px-2.5 py-1 rounded-full text-xs text-rose-300">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <span className="font-medium">Engine Offline</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
