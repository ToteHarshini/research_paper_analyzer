import React from 'react';
import { 
  PlusCircle, 
  BookOpen, 
  History, 
  FileText, 
  Server, 
  Settings2, 
  Sparkles,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function Sidebar({
  onNewResearch,
  uploadedPapers,
  history,
  onSelectHistory,
  activeHistoryId,
  backendStatus
}) {
  const isHealthy = backendStatus?.status === 'healthy';

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-violet))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Sparkles size={20} color="#FFFFFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#FFFFFF' }}>
              Research<span style={{ color: 'var(--accent-violet)' }}>AI</span>
            </h1>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: '500' }}>
              Agentic Literature Engine
            </p>
          </div>
        </div>

        {/* New Research Button */}
        <button
          onClick={onNewResearch}
          className="btn-primary"
          style={{ width: '100%', marginTop: '20px', padding: '10px 16px', fontSize: '0.88rem' }}
        >
          <PlusCircle size={17} />
          New Research
        </button>
      </div>

      {/* Nav Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 12px' }}>
        {/* Uploaded Papers Section */}
        {uploadedPapers && uploadedPapers.length > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0 8px 8px', color: 'var(--text-dim)', fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <BookOpen size={14} />
              Active Papers ({uploadedPapers.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {uploadedPapers.map((paper, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.82rem',
                    color: 'var(--text-main)',
                  }}
                >
                  <FileText size={15} color="var(--accent-indigo)" style={{ flexShrink: 0 }} />
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                    <div style={{ fontWeight: '500' }}>{paper.name || paper.title}</div>
                    {paper.size && (
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                        {(paper.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Investigation History */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0 8px 8px', color: 'var(--text-dim)', fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <History size={14} />
            Research History
          </div>

          {history && history.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {history.map((item) => {
                const isActive = activeHistoryId === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectHistory(item)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      background: isActive ? 'var(--bg-card-hover)' : 'transparent',
                      border: isActive ? '1px solid var(--accent-indigo)' : '1px solid transparent',
                      color: isActive ? '#FFFFFF' : 'var(--text-muted)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{
                      fontWeight: '500',
                      fontSize: '0.82rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      width: '100%'
                    }}>
                      {item.question}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '3px' }}>
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {item.filesCount || 1} paper(s)
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '16px 8px', fontSize: '0.8rem', color: 'var(--text-dim)', textAlign: 'center' }}>
              No previous research sessions yet.
            </div>
          )}
        </div>
      </div>

      {/* Backend Status Footer */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(0,0,0,0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isHealthy ? '#10B981' : '#EF4444',
            boxShadow: isHealthy ? '0 0 8px #10B981' : '0 0 8px #EF4444'
          }} />
          <div style={{ fontSize: '0.78rem' }}>
            <span style={{ color: isHealthy ? 'var(--text-main)' : '#F87171', fontWeight: '600' }}>
              {isHealthy ? 'Backend Online' : 'Backend Offline'}
            </span>
            {backendStatus?.llm_provider && (
              <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.7rem' }}>
                Provider: {backendStatus.llm_provider.toUpperCase()}
              </span>
            )}
          </div>
        </div>

        <div title="FastAPI Engine v1.0.0" style={{ color: 'var(--text-dim)' }}>
          <Server size={16} />
        </div>
      </div>
    </aside>
  );
}
