import React, { useState } from 'react';
import { 
  Cpu, 
  Database, 
  BarChart3, 
  Layers, 
  AlertOctagon, 
  FileText,
  Search,
  BookOpen,
  Hash
} from 'lucide-react';

const CATEGORY_META = {
  models: { label: 'Models & Architectures', icon: Cpu, color: '#818CF8' },
  datasets: { label: 'Datasets & Benchmarks', icon: Database, color: '#38BDF8' },
  performance: { label: 'Performance & Metrics', icon: BarChart3, color: '#34D399' },
  methodology: { label: 'Methodology & Setup', icon: Layers, color: '#F472B6' },
  limitations: { label: 'Limitations & Risks', icon: AlertOctagon, color: '#FBBF24' },
};

export default function FindingsTab({ structuredFindings }) {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  if (!structuredFindings || structuredFindings.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <Layers size={40} color="var(--text-dim)" style={{ margin: '0 auto 12px' }} />
        <h4 style={{ fontSize: '1.1rem', color: '#F8FAFC', fontWeight: '600' }}>No Structured Findings</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
          The structured extractor agent found no explicit entity entries across the analyzed passages.
        </p>
      </div>
    );
  }

  // Categories present in findings
  const availableCategories = Array.from(
    new Set(structuredFindings.map((f) => (f.category || '').toLowerCase()))
  );

  const filteredFindings = structuredFindings.filter((item) => {
    const cat = (item.category || '').toLowerCase();
    const catMatch = activeCategory === 'ALL' || cat === activeCategory;
    const query = searchQuery.toLowerCase();
    const contentMatch = !query || 
      (item.finding && item.finding.toLowerCase().includes(query)) ||
      (cat && cat.includes(query));
    return catMatch && contentMatch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#F8FAFC' }}>
            Structured Scientific Findings ({structuredFindings.length})
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            Systematically extracted entities categorized by model, dataset, methodology, and empirical metrics.
          </p>
        </div>

        {/* Category Filters */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <button
            onClick={() => setActiveCategory('ALL')}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: '600',
              cursor: 'pointer',
              background: activeCategory === 'ALL' ? 'var(--accent-indigo)' : 'rgba(255, 255, 255, 0.04)',
              color: activeCategory === 'ALL' ? '#FFFFFF' : 'var(--text-muted)',
              border: activeCategory === 'ALL' ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
              transition: 'all 0.15s ease'
            }}
          >
            All Categories ({structuredFindings.length})
          </button>
          {availableCategories.map((catKey) => {
            const meta = CATEGORY_META[catKey] || { label: catKey, color: '#A5B4FC' };
            const count = structuredFindings.filter((f) => (f.category || '').toLowerCase() === catKey).length;
            const isActive = activeCategory === catKey;
            return (
              <button
                key={catKey}
                onClick={() => setActiveCategory(catKey)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  background: isActive ? 'var(--accent-indigo)' : 'rgba(255, 255, 255, 0.04)',
                  color: isActive ? '#FFFFFF' : 'var(--text-muted)',
                  border: isActive ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                  transition: 'all 0.15s ease'
                }}
              >
                {meta.label} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Search Input */}
      <div style={{ position: 'relative' }}>
        <Search size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter findings by text or category..."
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

      {/* Findings Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(420px, 1fr))', gap: '14px' }}>
        {filteredFindings.length === 0 ? (
          <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
            No findings match the active filters.
          </div>
        ) : (
          filteredFindings.map((item, idx) => {
            const cat = (item.category || '').toLowerCase();
            const meta = CATEGORY_META[cat] || { label: cat, icon: Layers, color: '#A5B4FC' };
            const Icon = meta.icon;

            return (
              <div
                key={idx}
                className="glass-panel"
                style={{
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '14px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <div style={{
                      width: '26px',
                      height: '26px',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: meta.color
                    }}>
                      <Icon size={14} />
                    </div>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: '700',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      color: meta.color
                    }}>
                      {meta.label}
                    </span>
                  </div>

                  <p style={{
                    fontSize: '0.92rem',
                    color: '#F1F5F9',
                    lineHeight: '1.5',
                    fontWeight: '500'
                  }}>
                    {item.finding}
                  </p>
                </div>

                {/* Sources list */}
                {item.sources && item.sources.length > 0 && (
                  <div style={{
                    paddingTop: '10px',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: '600', textTransform: 'uppercase' }}>
                      Supporting Passages:
                    </span>
                    {item.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '8px',
                          fontSize: '0.76rem',
                          color: 'var(--text-muted)',
                          background: 'rgba(0, 0, 0, 0.2)',
                          padding: '4px 8px',
                          borderRadius: '4px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
                          <BookOpen size={12} color="var(--accent-indigo)" style={{ flexShrink: 0 }} />
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {src.paper_title || 'Document'}
                          </span>
                          {src.section && (
                            <span style={{ color: 'var(--text-dim)' }}>
                              • {src.section}
                            </span>
                          )}
                          {src.page_number && (
                            <span style={{ color: 'var(--text-dim)' }}>
                              (p. {src.page_number})
                            </span>
                          )}
                        </div>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.7rem',
                          color: 'var(--accent-violet)',
                          flexShrink: 0
                        }}>
                          {src.citation_id}
                        </span>
                      </div>
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
