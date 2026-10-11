import React from 'react';
import {
  Settings,
  Shield,
  Cpu,
  Layers,
  FileText,
  AlertCircle,
  HelpCircle,
  CheckCircle,
} from 'lucide-react';
import { HealthResponse } from '../types';

interface ReportsSettingsPageProps {
  health: HealthResponse | null;
}

export const ReportsSettingsPage: React.FC<ReportsSettingsPageProps> = ({ health }) => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
        <div className="flex items-center space-x-2 text-xs text-cyan-400 font-semibold mb-1">
          <Settings className="w-4 h-4" />
          <span>System Architecture & Governance</span>
        </div>
        <h1 className="text-xl font-extrabold text-white tracking-tight">
          System Configuration, Model Licenses & Scientific Limits
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Technical specifications, model licensing, dataset mappings, and operational safety disclaimers.
        </p>
      </div>

      {/* Model & Licensing Dossier */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Layers className="w-5 h-5" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Machine Learning Model & License Terms
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <span className="text-slate-400 font-semibold">Pretrained Detection Architecture</span>
            <div className="font-mono text-cyan-300 font-bold text-sm">
              Ultralytics YOLOv8 Nano (yolov8n.pt)
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Trained on the Microsoft COCO benchmark dataset containing 80 object categories. Native traffic classes mapped:
              Car (ID 2), Motorcycle (ID 3), Bus (ID 5), Truck (ID 7), Bicycle (ID 1), Pedestrian (ID 0).
            </p>
          </div>

          <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
            <span className="text-slate-400 font-semibold">License & Commercial Rights</span>
            <div className="font-mono text-amber-300 font-bold text-sm">
              AGPL-3.0 (Ultralytics) / CC-BY 4.0 (COCO)
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Weights are distributed for research, prototyping, and open-source applications. Commercial deployment of YOLOv8
              without AGPL source disclosure requires an enterprise license from Ultralytics Inc.
            </p>
          </div>
        </div>
      </div>

      {/* Indian Traffic Specific Reality Check */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
        <div className="flex items-center space-x-2 text-amber-400">
          <AlertCircle className="w-5 h-5" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Indian Driving Domain Specifics: Auto-Rickshaws & Density
          </h2>
        </div>

        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
            <h4 className="font-bold text-white mb-1">Indigenous Vehicle Categorisation (Auto-Rickshaws & E-Rickshaws)</h4>
            <p className="text-slate-400 text-[11px]">
              The standard COCO dataset does <b>not</b> contain an "Auto-rickshaw" or "Three-wheeler" class. In default operation,
              YOLO maps three-wheelers to nearest visually similar classes (commonly Car, Motorcycle, or Bus).
              To preserve algorithmic integrity, this system documents this limitation rather than fabricating synthetic predictions.
              When fine-tuned Indian driving weights (e.g. IDD dataset) are mounted, the backend dynamically recognizes custom auto-rickshaw classes.
            </p>
          </div>

          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
            <h4 className="font-bold text-white mb-1">Camera Calibration & Physical Speed (km/h) Truthfulness</h4>
            <p className="text-slate-400 text-[11px]">
              In accordance with computer-vision standards, <b>this application does not report real-world vehicle speeds in km/h</b>.
              Estimating metric speed requires rigorous pinhole camera intrinsic/extrinsic calibration, ground plane homography matrix mapping,
              and known ground control point measurements. Without camera calibration, reported numbers would be pure fabrication.
              The application instead reports verifiable 2D displacement vectors (px/s) and trajectory directional alignments.
            </p>
          </div>

          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80">
            <h4 className="font-bold text-white mb-1">Direction Anomaly vs Legal Citation</h4>
            <p className="text-slate-400 text-[11px]">
              Flagged wrong-side and lane-crossing events represent statistical trajectory non-conformities calculated via cosine vector
              similarity. These events serve strictly as candidate evidence dossiers for certified law enforcement and traffic engineer review,
              not legally automated penalties.
            </p>
          </div>
        </div>
      </div>

      {/* Runtime Environment */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3">
        <div className="flex items-center space-x-2 text-cyan-400">
          <Cpu className="w-5 h-5" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Local Execution Environment
          </h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px]">OS</span>
            <div className="font-bold text-white mt-0.5">Windows 11</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px]">Backend Framework</span>
            <div className="font-bold text-white mt-0.5">FastAPI & Python 3.12</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px]">Database</span>
            <div className="font-bold text-white mt-0.5">SQLite Local DB</div>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px]">Report Engine</span>
            <div className="font-bold text-white mt-0.5">ReportLab 5.0 (PDF)</div>
          </div>
        </div>
      </div>
    </div>
  );
};
