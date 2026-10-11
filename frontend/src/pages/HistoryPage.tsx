import React, { useEffect, useState } from 'react';
import {
  History,
  Search,
  Play,
  FileText,
  FileDown,
  Trash2,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import { AnalysisRecordSummary } from '../types';

interface HistoryPageProps {
  onSelectAnalysis: (analysisId: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectAnalysis }) => {
  const [history, setHistory] = useState<AnalysisRecordSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getHistory(100);
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Delete analysis record #${id}?`)) {
      try {
        await api.deleteHistoryItem(id);
        setHistory(history.filter((h) => h.id !== id));
      } catch (err) {
        alert('Failed to delete analysis record.');
      }
    }
  };

  const filtered = history.filter(
    (h) =>
      h.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      h.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-cyan-400 font-semibold mb-1">
            <History className="w-4 h-4" />
            <span>SQLite Local Audit Trail</span>
          </div>
          <h1 className="text-xl font-extrabold text-white tracking-tight">
            Traffic Intelligence Run History ({history.length})
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete persistent log of analyzed image frames and multi-object tracked video sessions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by filename / ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 w-52"
            />
          </div>

          <button
            onClick={loadHistory}
            className="p-2 bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-lg text-xs font-semibold transition-colors"
            title="Refresh history"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
        {loading ? (
          <div className="text-center py-16 text-xs text-slate-500">Loading audit history...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 text-xs text-slate-500">
            No analysis runs found matching current filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Analysis ID</th>
                  <th className="py-3 px-4">Media File</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4 text-center">Vehicles</th>
                  <th className="py-3 px-4 text-center">Pedestrians</th>
                  <th className="py-3 px-4 text-center">Events</th>
                  <th className="py-3 px-4 text-center">Congestion</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => onSelectAnalysis(item.id)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-cyan-400">{item.id}</td>
                    <td className="py-3 px-4 font-semibold text-white truncate max-w-xs">{item.filename}</td>
                    <td className="py-3 px-4">
                      <span className="flex items-center space-x-1.5 text-slate-300">
                        {item.media_type === 'video' ? (
                          <Play className="w-3.5 h-3.5 text-cyan-400" />
                        ) : (
                          <FileText className="w-3.5 h-3.5 text-amber-400" />
                        )}
                        <span className="capitalize">{item.media_type}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(item.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-200">{item.total_vehicles}</td>
                    <td className="py-3 px-4 text-center text-slate-400">{item.total_pedestrians}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.events_count > 0 ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {item.events_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        item.congestion_level === 'High' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        item.congestion_level === 'Moderate' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      }`}>
                        {item.congestion_level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {item.report_pdf_url && (
                          <a
                            href={item.report_pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                            title="Download PDF Report"
                          >
                            <FileDown className="w-4 h-4" />
                          </a>
                        )}
                        <button
                          onClick={(e) => handleDelete(item.id, e)}
                          className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                          title="Delete Analysis"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        <ArrowRight className="w-4 h-4 text-slate-500 ml-1" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
