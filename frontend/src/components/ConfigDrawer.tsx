import React, { useState } from 'react';
import { Sliders, Plus, Trash2, Compass, Layers, Shield, Hash } from 'lucide-react';
import { LaneDefinition, CountingLineDefinition } from '../types';

interface ConfigDrawerProps {
  confidence: number;
  onConfidenceChange: (val: number) => void;
  sampleStride: number;
  onSampleStrideChange: (val: number) => void;
  direction: string;
  onDirectionChange: (dir: string) => void;
  roadRoi: number[] | null;
  onRoadRoiChange: (roi: number[] | null) => void;
  lanes: LaneDefinition[];
  onLanesChange: (lanes: LaneDefinition[]) => void;
  countingLines: CountingLineDefinition[];
  onCountingLinesChange: (lines: CountingLineDefinition[]) => void;
}

export const ConfigDrawer: React.FC<ConfigDrawerProps> = ({
  confidence,
  onConfidenceChange,
  sampleStride,
  onSampleStrideChange,
  direction,
  onDirectionChange,
  roadRoi,
  onRoadRoiChange,
  lanes,
  onLanesChange,
  countingLines,
  onCountingLinesChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Helper to add a default lane
  const addLane = () => {
    const newLane: LaneDefinition = {
      id: `lane_${Date.now() % 1000}`,
      name: `Carriageway Lane ${lanes.length + 1}`,
      bounds: [0.0, 0.0, 0.5, 1.0],
      permitted_direction: direction,
    };
    onLanesChange([...lanes, newLane]);
  };

  // Helper to remove lane
  const removeLane = (id: string) => {
    onLanesChange(lanes.filter((l) => l.id !== id));
  };

  // Helper to add counting line
  const addCountingLine = () => {
    const newLine: CountingLineDefinition = {
      id: `line_${Date.now() % 1000}`,
      name: `Counting Line ${countingLines.length + 1}`,
      coords: [0.0, 0.5, 1.0, 0.5],
      direction_check: 'both',
    };
    onCountingLinesChange([...countingLines, newLine]);
  };

  // Helper to remove counting line
  const removeCountingLine = (id: string) => {
    onCountingLinesChange(countingLines.filter((l) => l.id !== id));
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-slate-800/80 hover:bg-slate-800 flex items-center justify-between text-left transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Analysis Rules & Corridor Configuration
          </span>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          {isOpen ? 'Collapse Controls ▲' : 'Configure Rules & Thresholds ▼'}
        </span>
      </button>

      {isOpen && (
        <div className="p-5 space-y-6 border-t border-slate-800 bg-slate-950/40">
          {/* 1. Basic sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Confidence Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Detection Confidence</span>
                <span className="text-cyan-400 font-bold">{Math.round(confidence * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.80"
                step="0.05"
                value={confidence}
                onChange={(e) => onConfidenceChange(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">Lower = detects more vehicles, higher = stricter accuracy.</p>
            </div>

            {/* Video Sample Stride */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Video Frame Stride</span>
                <span className="text-cyan-400 font-bold">Every {sampleStride} frame(s)</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={sampleStride}
                onChange={(e) => onSampleStrideChange(parseInt(e.target.value, 10))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">1 = full FPS (higher load), 2-3 = fast balanced tracking.</p>
            </div>

            {/* Expected Travel Direction */}
            <div className="space-y-1.5">
              <label className="text-xs text-slate-300 font-medium flex items-center space-x-1">
                <Compass className="w-3.5 h-3.5 text-cyan-400" />
                <span>Default Permitted Flow Direction</span>
              </label>
              <select
                value={direction}
                onChange={(e) => onDirectionChange(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="down">Downward (Top to Bottom)</option>
                <option value="up">Upward (Bottom to Top)</option>
                <option value="left">Leftward (Right to Left)</option>
                <option value="right">Rightward (Left to Right)</option>
              </select>
              <p className="text-[11px] text-slate-500">Vehicles moving against this flow are flagged for wrong-side audit.</p>
            </div>
          </div>

          {/* 2. Road ROI Corridor */}
          <div className="border-t border-slate-800/80 pt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-semibold text-slate-200">Active Road Corridor (ROI)</span>
              </div>
              <button
                type="button"
                onClick={() => onRoadRoiChange(roadRoi ? null : [0.05, 0.0, 0.95, 1.0])}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
              >
                {roadRoi ? 'Disable ROI (Use Full Frame)' : 'Enable Road Corridor ROI'}
              </button>
            </div>
            {roadRoi ? (
              <div className="grid grid-cols-4 gap-2 text-xs">
                <div>
                  <span className="text-slate-500 text-[10px]">X Min:</span>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={roadRoi[0]}
                    onChange={(e) => onRoadRoiChange([parseFloat(e.target.value), roadRoi[1], roadRoi[2], roadRoi[3]])}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Y Min:</span>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={roadRoi[1]}
                    onChange={(e) => onRoadRoiChange([roadRoi[0], parseFloat(e.target.value), roadRoi[2], roadRoi[3]])}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">X Max:</span>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={roadRoi[2]}
                    onChange={(e) => onRoadRoiChange([roadRoi[0], roadRoi[1], parseFloat(e.target.value), roadRoi[3]])}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Y Max:</span>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={roadRoi[3]}
                    onChange={(e) => onRoadRoiChange([roadRoi[0], roadRoi[1], roadRoi[2], parseFloat(e.target.value)])}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-white"
                  />
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-slate-500">Currently using the entire image frame as active roadway.</p>
            )}
          </div>

          {/* 3. Virtual Counting Lines */}
          <div className="border-t border-slate-800/80 pt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5">
                <Hash className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-semibold text-slate-200">Virtual Counting Lines</span>
              </div>
              <button
                type="button"
                onClick={addCountingLine}
                className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Counting Line</span>
              </button>
            </div>
            {countingLines.length === 0 ? (
              <p className="text-[11px] text-slate-500">No virtual counting lines configured. Add a virtual gate to record crossing events.</p>
            ) : (
              <div className="space-y-2">
                {countingLines.map((cl, i) => (
                  <div key={cl.id} className="flex items-center space-x-2 bg-slate-900 p-2 rounded-lg border border-slate-800 text-xs">
                    <input
                      type="text"
                      value={cl.name}
                      onChange={(e) => {
                        const updated = [...countingLines];
                        updated[i].name = e.target.value;
                        onCountingLinesChange(updated);
                      }}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white text-xs w-36"
                    />
                    <span className="text-slate-500 text-[10px]">Line Y:</span>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="1"
                      value={cl.coords[1]}
                      onChange={(e) => {
                        const updated = [...countingLines];
                        const val = parseFloat(e.target.value);
                        updated[i].coords = [0.0, val, 1.0, val];
                        onCountingLinesChange(updated);
                      }}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-white text-xs w-16"
                    />
                    <button
                      type="button"
                      onClick={() => removeCountingLine(cl.id)}
                      className="p-1 text-slate-400 hover:text-rose-400 transition-colors ml-auto"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
