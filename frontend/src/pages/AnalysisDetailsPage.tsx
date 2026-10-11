import React, { useState } from 'react';
import {
  Car,
  Users,
  AlertTriangle,
  FileDown,
  Clock,
  Layers,
  Info,
  Maximize2,
  Tag,
  Hash,
} from 'lucide-react';
import { StatsCard } from '../components/StatsCard';
import { VehicleCountsChart } from '../components/VehicleCountsChart';
import { CongestionGauge } from '../components/CongestionGauge';
import { TimeSeriesChart } from '../components/TimeSeriesChart';
import { EvidenceModal } from '../components/EvidenceModal';
import { ImageAnalysisResponse, VideoJobResult, TrafficEvent, CountingLineResult } from '../types';

interface AnalysisDetailsPageProps {
  data: ImageAnalysisResponse | VideoJobResult | null;
  onNavigateToEvents?: () => void;
}

export const AnalysisDetailsPage: React.FC<AnalysisDetailsPageProps> = ({ data, onNavigateToEvents }) => {
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null);
  const [viewMode, setViewMode] = useState<'annotated' | 'original'>('annotated');

  if (!data) {
    return (
      <div className="text-center py-20 border border-dashed border-slate-800 rounded-2xl">
        <Car className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h2 className="text-sm font-bold text-white">No Analysis Selected</h2>
        <p className="text-xs text-slate-400 mt-1">Upload a media file or select a past run from History.</p>
      </div>
    );
  }

  const isVideo = data.media_type === 'video';
  const vSummary = data.vehicle_summary;
  const events = data.events || [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
        <div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <span className="uppercase font-semibold text-cyan-400">{data.media_type} Analysis</span>
            <span>•</span>
            <span>ID: <code className="text-slate-300 font-mono">{data.analysis_id}</code></span>
            <span>•</span>
            <span>Processed in {data.processing_time_seconds.toFixed(2)}s</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <span>{data.filename}</span>
          </h1>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={data.report_pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-white text-xs font-semibold border border-slate-700 transition-colors shadow-sm"
          >
            <FileDown className="w-4 h-4 text-rose-400" />
            <span>Download PDF</span>
          </a>
          <a
            href={data.report_csv_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-white text-xs font-semibold border border-slate-700 transition-colors shadow-sm"
          >
            <FileDown className="w-4 h-4 text-emerald-400" />
            <span>Download CSV</span>
          </a>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Unique Vehicles"
          value={vSummary.unique_vehicles_total}
          subtitle="Persistent Tracked Entities"
          icon={Car}
          variant="cyan"
        />
        <StatsCard
          title="Pedestrians"
          value={data.total_pedestrians}
          subtitle="Road Exposure Detections"
          icon={Users}
          variant="emerald"
        />
        <StatsCard
          title="Congestion"
          value={data.congestion.level}
          subtitle={`${Math.round(data.congestion.occupancy_ratio * 100)}% Road Utilisation`}
          icon={Clock}
          variant={data.congestion.level === 'High' ? 'rose' : data.congestion.level === 'Moderate' ? 'amber' : 'emerald'}
        />
        <StatsCard
          title="Traffic Events"
          value={events.length}
          subtitle="Flagged Anomalies"
          icon={AlertTriangle}
          variant={events.length > 0 ? 'rose' : 'cyan'}
        />
      </div>

      {/* Media Player / Viewer & Vehicle Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Media Preview (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              {isVideo ? 'Annotated Video Playback' : 'Image Detection Inspection'}
            </h2>
            <div className="bg-slate-950 p-1 rounded-lg border border-slate-800 flex space-x-1 text-xs">
              <button
                onClick={() => setViewMode('annotated')}
                className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                  viewMode === 'annotated' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Annotated Stream
              </button>
              <button
                onClick={() => setViewMode('original')}
                className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                  viewMode === 'original' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Original Raw
              </button>
            </div>
          </div>

          <div className="bg-black rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center min-h-[360px]">
            {isVideo ? (
              <video
                src={viewMode === 'annotated' ? data.annotated_media_url : data.original_media_url}
                controls
                className="w-full max-h-[480px] object-contain"
              />
            ) : (
              <img
                src={viewMode === 'annotated' ? data.annotated_media_url : data.original_media_url}
                alt="Analyzed Traffic Frame"
                className="w-full max-h-[480px] object-contain"
              />
            )}
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
            <span>Dimensions: {isVideo ? (data as VideoJobResult).video_width : (data as ImageAnalysisResponse).image_width} × {isVideo ? (data as VideoJobResult).video_height : (data as ImageAnalysisResponse).image_height}</span>
            {isVideo && (
              <span>Analyzed {(data as VideoJobResult).frames_analyzed} / {(data as VideoJobResult).total_frames} frames ({((data as VideoJobResult).duration_seconds).toFixed(1)}s)</span>
            )}
          </div>
        </div>

        {/* Charts and Congestion (1 col) */}
        <div className="space-y-6">
          {/* Class counts breakdown */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Vehicle Classification Volume
            </h3>
            <VehicleCountsChart classCounts={data.class_counts} />
          </div>

          {/* Congestion assessment */}
          <CongestionGauge congestion={data.congestion} />
        </div>
      </div>

      {/* Video Timeline & Counting Line Results */}
      {isVideo && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Traffic Density & Flow Progression Timeline
            </h3>
            <TimeSeriesChart timeline={(data as VideoJobResult).per_frame_timeline} />
          </div>

          {/* Counting lines table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
              Virtual Counting Line Gates
            </h3>
            {vSummary.counting_line_results.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">
                No virtual counting lines were configured for this video.
              </p>
            ) : (
              <div className="space-y-2">
                {vSummary.counting_line_results.map((cl: CountingLineResult) => (
                  <div key={cl.line_id} className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 text-xs">
                    <div className="font-bold text-white mb-1">{cl.line_name}</div>
                    <div className="grid grid-cols-3 gap-1 text-[11px] text-slate-400">
                      <div>Forward: <b className="text-cyan-400">{cl.forward_count}</b></div>
                      <div>Reverse: <b className="text-amber-400">{cl.reverse_count}</b></div>
                      <div>Total: <b className="text-white">{cl.total_crossings}</b></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flagged Events Mini-Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Flagged Potential Traffic Events ({events.length})
            </h2>
            <p className="text-xs text-slate-400">Click any row to open the high-resolution evidence crop and vector explanation</p>
          </div>
          {onNavigateToEvents && (
            <button
              onClick={onNavigateToEvents}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
            >
              Full Events View →
            </button>
          )}
        </div>

        {events.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
            No direction anomalies or lane violations detected in this footage.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Time</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Track / Class</th>
                  <th className="py-2.5 px-3">Evidence Explanation</th>
                  <th className="py-2.5 px-3 text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {events.map((ev: TrafficEvent) => (
                  <tr
                    key={ev.id}
                    onClick={() => setSelectedEvent(ev)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 font-mono text-slate-300">{ev.timestamp_seconds.toFixed(1)}s</td>
                    <td className="py-2.5 px-3 font-semibold text-white capitalize">{ev.event_type.replace('_', ' ')}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ev.severity === 'critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {ev.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">#{ev.track_id ?? 'N/A'} {ev.vehicle_type ?? 'Vehicle'}</td>
                    <td className="py-2.5 px-3 text-slate-400 max-w-md truncate">{ev.reason}</td>
                    <td className="py-2.5 px-3 text-right">
                      <button className="text-cyan-400 hover:text-cyan-300 font-semibold text-[11px]">
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Known Limitations Alert */}
      {data.limitations && data.limitations.length > 0 && (
        <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl text-xs space-y-1.5 text-slate-400">
          <div className="flex items-center space-x-1.5 text-slate-300 font-semibold mb-1">
            <Info className="w-4 h-4 text-cyan-400" />
            <span>Operational Context & Technical Limitations</span>
          </div>
          {data.limitations.map((lim: string, idx: number) => (
            <div key={idx} className="flex items-start space-x-2">
              <span className="text-cyan-500">•</span>
              <span>{lim}</span>
            </div>
          ))}
        </div>
      )}

      {/* Evidence Crop Modal */}
      <EvidenceModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
};
