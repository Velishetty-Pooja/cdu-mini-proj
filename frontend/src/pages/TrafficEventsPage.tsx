import React, { useState } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  Eye,
  Clock,
  Hash,
  Tag,
  ShieldAlert,
} from 'lucide-react';
import { EvidenceModal } from '../components/EvidenceModal';
import { TrafficEvent } from '../types';

interface TrafficEventsPageProps {
  events: TrafficEvent[];
}

export const TrafficEventsPage: React.FC<TrafficEventsPageProps> = ({ events }) => {
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredEvents = events.filter((ev) => {
    const matchesFilter = filterType === 'all' || ev.event_type === filterType;
    const matchesSearch =
      searchQuery === '' ||
      ev.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.reason.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ev.vehicle_type && ev.vehicle_type.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (ev.track_id && ev.track_id.toString().includes(searchQuery));
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs text-rose-400 font-semibold mb-1">
              <ShieldAlert className="w-4 h-4" />
              <span>Evidence-Based Trajectory Violations</span>
            </div>
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              Traffic Events & Anomalies Log ({events.length})
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Auditable register of potential wrong-side movements, lane infractions, and stopped vehicle flow obstructions.
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Search */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search events, track ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 w-48"
              />
            </div>

            {/* Filter by Type */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Event Types</option>
              <option value="wrong_side">Wrong-Side Flow</option>
              <option value="lane_violation">Lane Violation</option>
              <option value="restricted_entry">Restricted Zone</option>
              <option value="stopped_vehicle">Stopped Vehicle</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events Table / Card List */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
          <AlertTriangle className="w-9 h-9 text-slate-600 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-white">No Matching Traffic Events</h3>
          <p className="text-xs text-slate-400 mt-1">
            {events.length === 0
              ? 'No traffic events have been flagged in current footage.'
              : 'Try clearing your search query or filter selection.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredEvents.map((ev) => (
            <div
              key={ev.id}
              onClick={() => setSelectedEvent(ev)}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl cursor-pointer transition-all shadow-md hover:scale-[1.01] space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    ev.severity === 'critical' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                  }`}>
                    {ev.severity.toUpperCase()}
                  </span>
                  <span className="text-xs font-bold text-white capitalize">
                    {ev.event_type.replace('_', ' ')}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  {ev.timestamp_seconds.toFixed(2)}s (F#{ev.frame_number})
                </span>
              </div>

              {/* Vehicle & Rule */}
              <div className="flex items-center justify-between text-xs text-slate-300">
                <div className="flex items-center space-x-1.5">
                  <Hash className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Track #{ev.track_id ?? 'N/A'} ({ev.vehicle_type ?? 'Vehicle'})</span>
                </div>
                <span className="text-[11px] text-slate-400">{ev.rule_name}</span>
              </div>

              {/* Mathematical / Trajectory Explanation */}
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 font-mono text-[11px]">
                {ev.reason}
              </p>

              <div className="flex items-center justify-between pt-1 text-xs">
                <span className="text-[10px] text-slate-500">{ev.id}</span>
                <span className="text-cyan-400 font-semibold flex items-center space-x-1 hover:text-cyan-300">
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Evidence Dossier</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Evidence Modal */}
      <EvidenceModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
};
