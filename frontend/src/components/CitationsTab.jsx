import React, { useState } from 'react';
import { 
  FileText, 
  Search, 
  Copy, 
  Check, 
  Hash, 
  BookOpen, 
  Sparkles,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';

export default function CitationsTab({ evidence, verifiedClaims }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  if (!evidence || evidence.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <FileText size={40} color="var(--text-dim)" style={{ margin: '0 auto 12px' }} />
        <h4 style={{ fontSize: '1.1rem', color: '#F8FAFC', fontWeight: '600' }}>No Evidence Passages</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
          No retrieved passages are available for this session.
        </p>
      </div>
    );
  }

  // Build a lookup map of citation_id -> list of claim verifications that cited this chunk
  const citationsInClaims = {};
  if (verifiedClaims && Array.isArray(verifiedClaims)) {
    verifiedClaims.forEach((claim) => {
      if (claim.citations && Array.isArray(claim.citations)) {
        claim.citations.forEach((cId) => {
          if (!citationsInClaims[cId]) {
            citationsInClaims[cId] = [];
          }
          citationsInClaims[cId].push(claim);
        });
      }
    });
  }

  const handleCopyPassage = (text, chunkId) => {
    navigator.clipboard.writeText(text);
    setCopiedId(chunkId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredEvidence = evidence.filter((item) => {
    const chunk = item.chunk || item;
    const query = searchQuery.toLowerCase();
    if (!query) return true;
    return (
      (chunk.text && chunk.text.toLowerCase().includes(query)) ||
      (chunk.paper_title && chunk.paper_title.toLowerCase().includes(query)) ||
      (chunk.section && chunk.section.toLowerCase().includes(query)) ||
      (chunk.chunk_id && chunk.chunk_id.toLowerCase().includes(query))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#F8FAFC' }}>
            Retrieved Evidence & Passages ({evidence.length})
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            High-scoring passages selected by BM25 + ChromaDB hybrid retrieval and SentenceTransformers reranker.
          </p>
        </div>
      </div>

      {/* Search Input */}
      <div style={{ position: 'relative' }}>
        <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search within extracted passages, titles, or sections..."
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

      {/* Evidence Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {filteredEvidence.length === 0 ? (
          <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
            No evidence passages match your search query.
          </div>
        ) : (
          filteredEvidence.map((item, idx) => {
            const chunk = item.chunk || item;
            const score = typeof item.score === 'number' ? item.score : null;
            const citedByClaims = citationsInClaims[chunk.chunk_id] || [];

            return (
              <div
                key={chunk.chunk_id || idx}
                className="glass-panel"
                style={{
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                {/* Meta Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      background: 'rgba(99, 102, 241, 0.15)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      color: 'var(--accent-violet)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.74rem',
                      fontWeight: '600'
                    }}>
                      <Hash size={12} />
                      {chunk.chunk_id || `CHUNK_${idx + 1}`}
                    </span>

                    <span style={{ fontSize: '0.88rem', fontWeight: '600', color: '#F8FAFC' }}>
                      {chunk.paper_title || 'Untitled Document'}
                    </span>

                    {chunk.section && (
                      <span style={{
                        fontSize: '0.76rem',
                        color: 'var(--text-muted)',
                        background: 'rgba(255, 255, 255, 0.04)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        border: '1px solid var(--border-subtle)'
                      }}>
                        Section: {chunk.section}
                      </span>
                    )}

                    {chunk.page_number && (
                      <span style={{ fontSize: '0.76rem', color: 'var(--text-dim)' }}>
                        Page {chunk.page_number}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {score !== null && (
                      <span
                        title="Cross-Encoder Reranker Relevance Score"
                        style={{
                          fontSize: '0.74rem',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: 'rgba(52, 211, 153, 0.1)',
                          border: '1px solid rgba(52, 211, 153, 0.25)',
                          color: '#34D399',
                          fontWeight: '600',
                          fontFamily: 'var(--font-mono)'
                        }}
                      >
                        Score: {score.toFixed(3)}
                      </span>
                    )}
                    <button
                      onClick={() => handleCopyPassage(chunk.text, chunk.chunk_id)}
                      title="Copy passage text"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: copiedId === chunk.chunk_id ? '#34D399' : 'var(--text-dim)',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.74rem'
                      }}
                    >
                      {copiedId === chunk.chunk_id ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copiedId === chunk.chunk_id ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                </div>

                {/* Passage Text */}
                <div style={{
                  padding: '14px 16px',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.88rem',
                  lineHeight: '1.65',
                  color: '#CBD5E1',
                  fontFamily: 'inherit'
                }}>
                  {chunk.text}
                </div>

                {/* Verification cross-link if cited */}
                {citedByClaims.length > 0 && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.75rem',
                    color: 'var(--text-dim)',
                    paddingTop: '4px'
                  }}>
                    <ShieldCheck size={14} color="#34D399" />
                    <span>Cited in <strong>{citedByClaims.length}</strong> claim verification{citedByClaims.length > 1 ? 's' : ''}:</span>
                    {citedByClaims.map((claim, cIdx) => (
                      <span
                        key={cIdx}
                        className={`badge ${
                          claim.status === 'supported' ? 'badge-supported' :
                          claim.status === 'contradicted' ? 'badge-contradicted' :
                          claim.status === 'partially_supported' ? 'badge-partial' :
                          'badge-insufficient'
                        }`}
                        style={{ fontSize: '0.7rem', padding: '1px 6px' }}
                      >
                        {claim.status}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
