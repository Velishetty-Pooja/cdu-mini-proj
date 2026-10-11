import React, { useEffect, useState } from 'react';
import {
  Car,
  Users,
  AlertTriangle,
  Gauge,
  Upload,
  Play,
  FileText,
  Clock,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { StatsCard } from '../components/StatsCard';
import { api } from '../services/api';
import { HealthResponse, AnalysisRecordSummary } from '../types';

interface DashboardPageProps {
  health: HealthResponse | null;
  onNavigate: (tab: string, analysisId?: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ health, onNavigate }) => {
  const [history, setHistory] = useState<AnalysisRecordSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.getHistory(10);
        setHistory(data.history || []);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const totalAnalyses = history.length;
  const totalVehicles = history.reduce((sum, h) => sum + (h.total_vehicles || 0), 0);
  const totalEvents = history.reduce((sum, h) => sum + (h.events_count || 0), 0);
  const totalPedestrians = history.reduce((sum, h) => sum + (h.total_pedestrians || 0), 0);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-800/80 text-cyan-300 text-xs font-semibold mb-2">
            <span>Production Computer Vision</span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span>ByteTrack Engine</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Indian Traffic Intelligence Operations
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time object detection, persistent vehicle tracking, direction verification, lane discipline analysis, and density audit for Indian road corridors.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all shadow-lg shadow-cyan-600/20"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Traffic Media</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Analyses Run"
          value={totalAnalyses}
          subtitle="Persistent SQLite Records"
          icon={Clock}
          variant="cyan"
        />
        <StatsCard
          title="Unique Vehicles Tracked"
          value={totalVehicles}
          subtitle="Persistent IDs Counted"
          icon={Car}
          variant="amber"
        />
        <StatsCard
          title="Potential Traffic Events"
          value={totalEvents}
          subtitle="Wrong-Side & Lane Alerts"
          icon={AlertTriangle}
          variant="rose"
        />
        <StatsCard
          title="Pedestrians Observed"
          value={totalPedestrians}
          subtitle="Roadway Exposure Count"
          icon={Users}
          variant="emerald"
        />
      </div>

      {/* Main Grid: Recent Analyses & Model Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Analyses (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Recent Traffic Media Analyses
              </h2>
              <p className="text-xs text-slate-400">Past processed images and multi-frame video runs</p>
            </div>
            <button
              onClick={() => onNavigate('history')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center space-x-1"
            >
              <span>View Full History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12 text-xs text-slate-500">
              Loading recent analysis records...
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
              <Car className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400 font-medium">No traffic analyses recorded yet.</p>
              <button
                onClick={() => onNavigate('upload')}
                className="mt-3 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded-lg text-xs font-semibold"
              >
                Upload an image or video to begin
              </button>
            </div>
          ) : (
            <div className="space-y-2.5">
              {history.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  onClick={() => onNavigate('details', item.id)}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 cursor-pointer transition-all"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${item.media_type === 'video' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-amber-500/20 text-amber-400'}`}>
                      {item.media_type === 'video' ? <Play className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white flex items-center space-x-2">
                        <span className="truncate max-w-[200px]">{item.filename}</span>
                        <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                          {item.media_type}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5 flex items-center space-x-2">
                        <span>Vehicles: {item.total_vehicles}</span>
                        <span>•</span>
                        <span>Events: {item.events_count}</span>
                        <span>•</span>
                        <span className="text-slate-500">{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      item.congestion_level === 'High' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                      item.congestion_level === 'Moderate' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                      'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      {item.congestion_level}
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Engine Status & Limitations Card (1 col) */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
              Detection Engine Health
            </h2>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                <span className="text-slate-400">Model Weights:</span>
                <span className="font-mono text-cyan-400 font-semibold">{health?.model_name || 'Loading...'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                <span className="text-slate-400">Compute Device:</span>
                <span className="font-semibold text-white uppercase">{health?.device || 'CPU'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                <span className="text-slate-400">Tracker Algorithm:</span>
                <span className="font-semibold text-white">ByteTrack (Lapx Association)</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/80">
                <span className="text-slate-400">Supported Classes:</span>
                <span className="font-semibold text-emerald-400">{health?.classes_supported.length || 6} Classes</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded-2xl p-4">
            <div className="flex items-center space-x-2 text-amber-400 mb-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Methodology Integrity</h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              All counts and events originate strictly from real YOLO inference and ByteTrack position histories. Real-world speeds in km/h are not reported without metric camera calibration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
