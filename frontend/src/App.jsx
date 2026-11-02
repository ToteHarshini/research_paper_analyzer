import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, 
  RefreshCw, 
  Server, 
  Terminal, 
  Sparkles,
  ExternalLink 
} from 'lucide-react';

import Sidebar from './components/Sidebar';
import ResearchInput from './components/ResearchInput';
import AnalysisLoading from './components/AnalysisLoading';
import ResultsView from './components/ResultsView';
import { checkHealth, analyzePapers } from './services/api';

const STORAGE_KEY = 'research_ai_history_v1';

export default function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAnalysisMeta, setCurrentAnalysisMeta] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  
  // Load history from localStorage
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch (_) {
      return [];
    }
  });

  // Check health on mount
  const runHealthCheck = async () => {
    const status = await checkHealth();
    setBackendStatus(status);
  };

  useEffect(() => {
    runHealthCheck();
  }, []);

  // Sync history to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (_) {}
  }, [history]);

  const handleStartAnalysis = async (question, files) => {
    setIsAnalyzing(true);
    setError(null);
    setCurrentAnalysisMeta({
      question,
      filesCount: files.length,
      filesList: files.map((f) => ({ name: f.name, size: f.size })),
    });

    try {
      const response = await analyzePapers(question, files);

      const sessionResult = {
        id: `sess_${Date.now()}`,
        question,
        timestamp: new Date().toISOString(),
        filesCount: files.length,
        filesList: files.map((f) => ({ name: f.name, size: f.size })),
        final_report: response.final_report,
        subquestions: response.subquestions || [],
        verified_claims: response.verified_claims || [],
        structured_findings: response.structured_findings || [],
        evidence: response.evidence || [],
        papers_count: response.papers_count || files.length,
      };

      setResults(sessionResult);
      setActiveHistoryId(sessionResult.id);

      // Add to history
      setHistory((prev) => [sessionResult, ...prev]);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'An unexpected error occurred during paper analysis.');
    } finally {
      setIsAnalyzing(false);
      setCurrentAnalysisMeta(null);
    }
  };

  const handleNewResearch = () => {
    setResults(null);
    setActiveHistoryId(null);
    setError(null);
  };

  const handleSelectHistory = (item) => {
    setResults(item);
    setActiveHistoryId(item.id);
    setError(null);
  };

  // Extract active papers for sidebar
  const activePapers = results?.filesList || currentAnalysisMeta?.filesList || [];

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <Sidebar
        onNewResearch={handleNewResearch}
        uploadedPapers={activePapers}
        history={history}
        onSelectHistory={handleSelectHistory}
        activeHistoryId={activeHistoryId}
        backendStatus={backendStatus}
      />

      {/* Main Workspace Area */}
      <main className="main-content">
        {/* Top Backend Offline Warning Banner if unreachable */}
        {backendStatus?.status === 'unreachable' && (
          <div style={{
            background: 'linear-gradient(90deg, #991B1B 0%, #7F1D1D 100%)',
            color: '#FEE2E2',
            padding: '10px 24px',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(239, 68, 68, 0.4)',
            zIndex: 10
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={16} color="#FCA5A5" />
              <span>
                <strong>FastAPI backend is offline or unreachable on port 8000.</strong> Start it with:
                <code style={{ marginLeft: '6px', background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
                  uvicorn app:app --reload --port 8000
                </code>
              </span>
            </div>
            <button
              onClick={runHealthCheck}
              style={{
                background: 'rgba(255,255,255,0.15)',
                border: 'none',
                color: '#FFFFFF',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <RefreshCw size={12} />
              Retry Connection
            </button>
          </div>
        )}

        {/* Global Error Alert Banner */}
        {error && (
          <div style={{
            maxWidth: '860px',
            margin: '24px auto 0',
            width: '100%',
            padding: '14px 20px',
            borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            color: '#F87171',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            fontSize: '0.88rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <div>
                <strong style={{ display: 'block', color: '#FECACA' }}>Analysis Failed</strong>
                <span>{error}</span>
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#FCA5A5',
                cursor: 'pointer',
                fontSize: '0.8rem',
                textDecoration: 'underline'
              }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Main View Switcher */}
        {isAnalyzing ? (
          <AnalysisLoading
            question={currentAnalysisMeta?.question}
            filesCount={currentAnalysisMeta?.filesCount}
          />
        ) : results ? (
          <ResultsView
            results={results}
            onNewResearch={handleNewResearch}
          />
        ) : (
          <ResearchInput
            onStartAnalysis={handleStartAnalysis}
            isAnalyzing={isAnalyzing}
          />
        )}
      </main>
    </div>
  );
}
