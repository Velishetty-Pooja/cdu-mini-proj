import React from 'react';
import { X, AlertTriangle, Clock, Hash, Tag, FileText } from 'lucide-react';
import { TrafficEvent } from '../types';
import { getMediaUrl } from '../services/api';

interface EvidenceModalProps {
  event: TrafficEvent | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ event, onClose }) => {
  if (!event) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-2.5">
            <div className={`p-1.5 rounded-lg ${event.severity === 'critical' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Traffic Event Evidence Dossier
              </h3>
              <p className="text-xs text-slate-400">ID: {event.id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Evidence Frame Image */}
          {event.evidence_url ? (
            <div className="rounded-xl overflow-hidden border border-slate-800 bg-black flex items-center justify-center">
              <img
                src={getMediaUrl(event.evidence_url)}
                alt={`Evidence crop for ${event.id}`}
                className="max-h-64 object-contain"
              />
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 p-6 text-center text-xs text-slate-500">
              No crop image available for this event entry.
            </div>
          )}

          {/* Key Event Metadata */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                <Tag className="w-3.5 h-3.5 text-cyan-400" />
                <span>Event Type</span>
              </div>
              <div className="text-sm font-bold text-white capitalize">
                {event.event_type.replace('_', ' ')}
              </div>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Timestamp / Frame</span>
              </div>
              <div className="text-sm font-bold text-white">
                {event.timestamp_seconds.toFixed(2)}s (Frame #{event.frame_number})
              </div>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                <Hash className="w-3.5 h-3.5 text-cyan-400" />
                <span>Track ID & Vehicle</span>
              </div>
              <div className="text-sm font-bold text-white">
                #{event.track_id ?? 'N/A'} {event.vehicle_type ?? 'Vehicle'}
              </div>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                <span>Configured Rule</span>
              </div>
              <div className="text-sm font-bold text-white">
                {event.rule_name}
              </div>
            </div>
          </div>

          {/* Mathematical & Algorithmic Reason */}
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
            <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1.5">
              Evidence Basis & Trajectory Calculation
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed font-mono">
              {event.reason}
            </p>
          </div>

          {/* Legal disclaimer */}
          <div className="text-[11px] text-slate-500 italic">
            Note: This flagged event represents an algorithmic trajectory deviation. It is presented as candidate evidence for human operator adjudication and does not constitute a legally certified traffic citation.
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
