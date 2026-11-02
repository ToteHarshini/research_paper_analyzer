import React, { useState } from 'react';
import { 
  FileText, 
  ShieldCheck, 
  Layers, 
  BookOpen, 
  MessageSquare,
  ArrowLeft,
  Sparkles,
  Calendar,
  FileCheck
} from 'lucide-react';

import ReportTab from './ReportTab';
import ClaimsTab from './ClaimsTab';
import FindingsTab from './FindingsTab';
import CitationsTab from './CitationsTab';
import FollowUpChat from './FollowUpChat';

export default function ResultsView({ results, onNewResearch }) {
  const [activeTab, setActiveTab] = useState('report');

  const question = results?.question || 'Literature Investigation';
  const finalReport = results?.final_report || '';
  const subquestions = results?.subquestions || [];
  const verifiedClaims = results?.verified_claims || [];
  const structuredFindings = results?.structured_findings || [];
  const evidence = results?.evidence || [];
  const papersCount = results?.papers_count || results?.files_count || 1;

  const tabs = [
    { id: 'report', label: 'Executive Report', icon: FileText, count: null },
    { id: 'claims', label: 'Verified Claims', icon: ShieldCheck, count: verifiedClaims.length },
    { id: 'findings', label: 'Structured Findings', icon: Layers, count: structuredFindings.length },
    { id: 'citations', label: 'Evidence & Citations', icon: BookOpen, count: evidence.length },
    { id: 'chat', label: 'Follow-Up Chat', icon: MessageSquare, count: null },
  ];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Investigation Summary Header */}
      <div className="glass-panel" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <button
            onClick={onNewResearch}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-dim)',
              fontSize: '0.82rem',
              cursor: 'pointer',
              padding: '0'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#FFFFFF')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
          >
            <ArrowLeft size={14} />
            <span>Start Another Research Query</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 10px',
              borderRadius: '9999px',
              background: 'rgba(52, 211, 153, 0.12)',
              border: '1px solid rgba(52, 211, 153, 0.3)',
              color: '#34D399',
              fontSize: '0.74rem',
              fontWeight: '600'
            }}>
              <FileCheck size={12} />
              Synthesis Complete
            </span>
          </div>
        </div>

        <h2 style={{ fontSize: '1.45rem', fontWeight: '800', color: '#F8FAFC', letterSpacing: '-0.01em', lineHeight: '1.35', marginBottom: '12px' }}>
          {question}
        </h2>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <BookOpen size={14} color="var(--accent-indigo)" />
            <span>{papersCount} Research Paper{papersCount === 1 ? '' : 's'} Analyzed</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <ShieldCheck size={14} color="#34D399" />
            <span>{verifiedClaims.length} Claims Verified</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Layers size={14} color="var(--accent-violet)" />
            <span>{structuredFindings.length} Structured Entities</span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '2px',
        overflowX: 'auto',
      }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${isActive ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span style={{
                  padding: '1px 6px',
                  borderRadius: '9999px',
                  background: isActive ? 'var(--accent-violet)' : 'rgba(255, 255, 255, 0.08)',
                  color: '#FFFFFF',
                  fontSize: '0.72rem',
                  fontWeight: '700'
                }}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content Display */}
      <div style={{ minHeight: '400px' }}>
        {activeTab === 'report' && (
          <ReportTab finalReport={finalReport} subquestions={subquestions} />
        )}
        {activeTab === 'claims' && (
          <ClaimsTab verifiedClaims={verifiedClaims} />
        )}
        {activeTab === 'findings' && (
          <FindingsTab structuredFindings={structuredFindings} />
        )}
        {activeTab === 'citations' && (
          <CitationsTab evidence={evidence} verifiedClaims={verifiedClaims} />
        )}
        {activeTab === 'chat' && (
          <FollowUpChat finalReport={finalReport} evidence={evidence} />
        )}
      </div>
    </div>
  );
}
