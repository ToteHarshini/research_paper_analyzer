import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  FileText, 
  Copy, 
  Check, 
  GitBranch, 
  ChevronDown, 
  ChevronUp, 
  Share2 
} from 'lucide-react';

export default function ReportTab({ finalReport, subquestions }) {
  const [copied, setCopied] = useState(false);
  const [showSubquestions, setShowSubquestions] = useState(true);

  const handleCopy = () => {
    if (!finalReport) return;
    navigator.clipboard.writeText(finalReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Action Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#F8FAFC' }}>
            Executive Synthesis Report
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            Grounded multi-paper synthesis compiled by the Report Generator agent.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleCopy}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
          >
            {copied ? (
              <>
                <Check size={14} color="#34D399" />
                <span style={{ color: '#34D399' }}>Copied</span>
              </>
            ) : (
              <>
                <Copy size={14} />
                <span>Copy Markdown</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Planner Subquestions Bar */}
      {subquestions && subquestions.length > 0 && (
        <div className="glass-panel" style={{ padding: '16px 20px' }}>
          <div 
            onClick={() => setShowSubquestions(!showSubquestions)}
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              cursor: 'pointer',
              userSelect: 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GitBranch size={16} color="var(--accent-indigo)" />
              <span style={{ fontSize: '0.88rem', fontWeight: '600', color: 'var(--text-main)' }}>
                Planner Decomposed Subquestions ({subquestions.length})
              </span>
            </div>
            <div style={{ color: 'var(--text-dim)' }}>
              {showSubquestions ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>
          </div>

          {showSubquestions && (
            <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {subquestions.map((subq, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '0.84rem',
                    color: 'var(--text-muted)'
                  }}
                >
                  <span style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    background: 'rgba(99, 102, 241, 0.15)',
                    color: 'var(--accent-indigo)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.72rem',
                    fontWeight: '700',
                    flexShrink: 0
                  }}>
                    {idx + 1}
                  </span>
                  <span style={{ flex: 1, lineHeight: '1.4' }}>{subq}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Rendered Markdown Body */}
      <div className="glass-panel" style={{ padding: '32px 36px' }}>
        {finalReport ? (
          <div className="markdown-body">
            <ReactMarkdown>{finalReport}</ReactMarkdown>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
            No report content available.
          </div>
        )}
      </div>
    </div>
  );
}
