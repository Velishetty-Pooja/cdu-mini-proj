import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { AnalysisDetailsPage } from './pages/AnalysisDetailsPage';
import { TrafficEventsPage } from './pages/TrafficEventsPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsSettingsPage } from './pages/ReportsSettingsPage';
import { api } from './services/api';
import { HealthResponse, ImageAnalysisResponse, VideoJobResult } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [activeAnalysis, setActiveAnalysis] = useState<ImageAnalysisResponse | VideoJobResult | null>(null);

  // Check backend health on mount
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const h = await api.getHealth();
        setHealth(h);
      } catch (err) {
        console.error('Backend health check error:', err);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Handle drill down to specific analysis
  const handleSelectAnalysis = async (analysisId: string) => {
    try {
      const data = await api.getAnalysisResult(analysisId);
      if (data && data.result) {
        setActiveAnalysis(data.result);
        setCurrentTab('details');
      } else {
        alert('Could not retrieve full analysis result details.');
      }
    } catch (err) {
      console.error('Failed to load analysis:', err);
      alert('Failed to retrieve analysis from server.');
    }
  };

  const handleAnalysisComplete = (analysisId: string, resultData: any) => {
    setActiveAnalysis(resultData);
    setCurrentTab('details');
  };

  const handleTabChange = (tab: string) => {
    setCurrentTab(tab);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar currentTab={currentTab} onTabChange={handleTabChange} health={health} />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && (
          <DashboardPage
            health={health}
            onNavigate={(tab, id) => {
              if (id) {
                handleSelectAnalysis(id);
              } else {
                setCurrentTab(tab);
              }
            }}
          />
        )}

        {currentTab === 'upload' && (
          <UploadPage onAnalysisComplete={handleAnalysisComplete} />
        )}

        {currentTab === 'details' && (
          <AnalysisDetailsPage
            data={activeAnalysis}
            onNavigateToEvents={() => setCurrentTab('events')}
          />
        )}

        {currentTab === 'events' && (
          <TrafficEventsPage events={activeAnalysis?.events || []} />
        )}

        {currentTab === 'history' && (
          <HistoryPage onSelectAnalysis={handleSelectAnalysis} />
        )}

        {currentTab === 'settings' && (
          <ReportsSettingsPage health={health} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Indian Traffic Intelligence • Production Computer Vision Prototype</span>
          <span className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>FastAPI Backend: 127.0.0.1:8000</span>
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
