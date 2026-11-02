import React, { useState } from 'react';
import { 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle,
  Search,
  Hash
} from 'lucide-react';

export default function ClaimsTab({ verifiedClaims }) {
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  if (!verifiedClaims || verifiedClaims.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <ShieldCheck size={40} color="var(--text-dim)" style={{ margin: '0 auto 12px' }} />
        <h4 style={{ fontSize: '1.1rem', color: '#F8FAFC', fontWeight: '600' }}>No Claims Verified</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
          No explicit empirical claims were extracted for verification in this session.
        </p>
      </div>
    );
  }

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'supported':
        return (
          <span className="badge badge-supported">
            <CheckCircle2 size={13} />
            Supported
          </span>
        );
      case 'contradicted':
        return (
          <span className="badge badge-contradicted">
            <XCircle size={13} />
            Contradicted
          </span>
        );
      case 'partially_supported':
        return (
          <span className="badge badge-partial">
            <AlertTriangle size={13} />
            Partially Supported
          </span>
        );
      case 'insufficient_evidence':
      default:
        return (
          <span className="badge badge-insufficient">
            <HelpCircle size={13} />
            Insufficient Evidence
          </span>
        );
    }
  };

  const filteredClaims = verifiedClaims.filter((item) => {
    const statusMatch = filterStatus === 'ALL' || (item.status || '').toLowerCase() === filterStatus.toLowerCase();
    const query = searchQuery.toLowerCase();
    const contentMatch = !query || 
      (item.claim && item.claim.toLowerCase().includes(query)) ||
      (item.reason && item.reason.toLowerCase().includes(query));
    return statusMatch && contentMatch;
  });

  const countByStatus = {
    all: verifiedClaims.length,
    supported: verifiedClaims.filter(c => (c.status || '').toLowerCase() === 'supported').length,
    contradicted: verifiedClaims.filter(c => (c.status || '').toLowerCase() === 'contradicted').length,
    partially_supported: verifiedClaims.filter(c => (c.status || '').toLowerCase() === 'partially_supported').length,
    insufficient_evidence: verifiedClaims.filter(c => (c.status || '').toLowerCase() === 'insufficient_evidence').length,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#F8FAFC' }}>
            Verified Empirical Claims ({verifiedClaims.length})
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            Extracted claims verified against retrieved passages by the Verifier Agent to detect hallucinations.
          </p>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {[
            { id: 'ALL', label: `All (${countByStatus.all})` },
            { id: 'supported', label: `Supported (${countByStatus.supported})` },
            { id: 'partially_supported', label: `Partial (${countByStatus.partially_supported})` },
            { id: 'contradicted', label: `Contradicted (${countByStatus.contradicted})` },
            { id: 'insufficient_evidence', label: `Insufficient (${countByStatus.insufficient_evidence})` },
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => setFilterStatus(btn.id)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                fontWeight: '600',
                cursor: 'pointer',
                background: filterStatus === btn.id ? 'var(--accent-indigo)' : 'rgba(255, 255, 255, 0.04)',
                color: filterStatus === btn.id ? '#FFFFFF' : 'var(--text-muted)',
                border: filterStatus === btn.id ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                transition: 'all 0.15s ease'
              }}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div style={{ position: 'relative' }}>
        <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter verified claims by keyword or reason..."
          style={{
            width: '100%',
            padding: '10px 14px 10px 40px',
            borderRadius: '8px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            color: '#FFFFFF',
            fontSize: '0.85rem',
            outline: 'none',
          }}
        />
      </div>

      {/* Claims List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredClaims.length === 0 ? (
          <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
            No claims match the active filter or search query.
          </div>
        ) : (
          filteredClaims.map((item, idx) => (
            <div
              key={idx}
              className="glass-panel"
              style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ fontSize: '0.98rem', fontWeight: '600', color: '#F8FAFC', lineHeight: '1.45', flex: 1 }}>
                  {item.claim}
                </div>
                <div>{getStatusBadge(item.status)}</div>
              </div>

              {item.reason && (
                <div style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.25)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.85rem',
                  color: 'var(--text-muted)',
                  lineHeight: '1.5'
                }}>
                  <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '4px', fontSize: '0.76rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Verification Analysis
                  </strong>
                  {item.reason}
                </div>
              )}

              {item.citations && item.citations.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', paddingTop: '4px' }}>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)', fontWeight: '600' }}>
                    CITED SOURCES:
                  </span>
                  {item.citations.map((citeId, cIdx) => (
                    <span
                      key={cIdx}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '3px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.25)',
                        fontSize: '0.72rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--accent-violet)',
                        fontWeight: '500'
                      }}
                    >
                      <Hash size={11} />
                      {citeId}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
