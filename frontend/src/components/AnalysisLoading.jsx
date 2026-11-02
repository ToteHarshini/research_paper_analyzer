import React, { useState, useEffect } from 'react';
import { 
  Loader2, 
  Cpu, 
  FileSearch, 
  Layers, 
  Binary, 
  Search, 
  Filter, 
  ShieldCheck, 
  FileCheck2,
  Clock
} from 'lucide-react';

const PIPELINE_STAGES = [
  { id: 1, name: 'PDF Parsing', desc: 'PyMuPDF structural text extraction', icon: FileSearch },
  { id: 2, name: 'Section Extraction', desc: 'Abstract, Intro, Method, Results & Limitations', icon: Layers },
  { id: 3, name: 'Chunking & Tokenization', desc: 'Heading-aware semantic sliding window', icon: Binary },
  { id: 4, name: 'Embeddings Generation', desc: 'HuggingFace MiniLM dense representations', icon: Cpu },
  { id: 5, name: 'Hybrid Retrieval', desc: 'BM25 keyword + ChromaDB vector search', icon: Search },
  { id: 6, name: 'Cross-Encoder Reranking', desc: 'SentenceTransformers contextual scoring', icon: Filter },
  { id: 7, name: 'Claim Verification', desc: 'Evidence-grounded hallucination checks', icon: ShieldCheck },
  { id: 8, name: 'Report Generation', desc: 'Multi-agent executive synthesis', icon: FileCheck2 },
];

export default function AnalysisLoading({ question, filesCount }) {
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', width: '100%', padding: '48px 24px' }}>
      {/* Central Spinner Card */}
      <div className="glass-panel" style={{ padding: '36px 32px', textAlign: 'center', marginBottom: '32px' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          boxShadow: '0 0 30px rgba(99, 102, 241, 0.3)'
        }}>
          <Loader2 size={32} color="var(--accent-indigo)" className="spin-slow" />
        </div>

        <h3 style={{ fontSize: '1.45rem', fontWeight: '700', color: '#F8FAFC', marginBottom: '8px' }}>
          Agentic Analysis in Progress
        </h3>
        
        <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', maxWidth: '580px', margin: '0 auto 16px' }}>
          Analyzing <strong>{filesCount} paper{filesCount === 1 ? '' : 's'}</strong> for inquiry:
          <span style={{ display: 'block', color: 'var(--text-main)', fontStyle: 'italic', marginTop: '6px' }}>
            "{question}"
          </span>
        </p>

        {/* Live Elapsed Counter (Genuine, not fake percent) */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          borderRadius: '9999px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.82rem',
          color: 'var(--text-dim)'
        }}>
          <Clock size={14} color="var(--accent-violet)" />
          <span>Elapsed Time: <strong>{secondsElapsed}s</strong></span>
        </div>
      </div>

      {/* 8 Pipeline Stages Overview */}
      <div className="glass-panel" style={{ padding: '28px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: '700', color: '#F8FAFC' }}>
              LangGraph Workflow Pipeline
            </h4>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '2px' }}>
              The multi-agent graph coordinates these 8 stages end-to-end. The view updates upon completion.
            </p>
          </div>
          <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: 'var(--accent-indigo)' }}>
            8 Continuous Stages
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
          {PIPELINE_STAGES.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(99, 102, 241, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-violet)',
                  flexShrink: 0
                }}>
                  <Icon size={16} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: '0.86rem', fontWeight: '600', color: 'var(--text-main)' }}>
                    {stage.id}. {stage.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    {stage.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
