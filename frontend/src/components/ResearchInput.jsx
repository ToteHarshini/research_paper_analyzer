import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  X, 
  Sparkles, 
  HelpCircle, 
  AlertCircle,
  Lightbulb
} from 'lucide-react';

const SUGGESTIONS = [
  "What are the core architectural mechanisms and technical innovations proposed?",
  "Synthesize the empirical findings, datasets, and benchmark results.",
  "What are the stated limitations, failure modes, and future research directions?",
  "Compare the methodological rigor, ablation studies, and baseline comparisons."
];

export default function ResearchInput({ onStartAnalysis, isAnalyzing }) {
  const [question, setQuestion] = useState('');
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);
  const isSubmittingRef = useRef(false);

  // Sync ref with isAnalyzing prop when analysis completes or resets
  React.useEffect(() => {
    if (!isAnalyzing) {
      isSubmittingRef.current = false;
    }
  }, [isAnalyzing]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFiles = (incomingFiles) => {
    setErrorMsg('');
    const validPdfs = [];
    let hasNonPdf = false;

    Array.from(incomingFiles).forEach((file) => {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        // Avoid duplicate by name & size
        const exists = files.some((f) => f.name === file.name && f.size === file.size);
        if (!exists) {
          validPdfs.push(file);
        }
      } else {
        hasNonPdf = true;
      }
    });

    if (hasNonPdf) {
      setErrorMsg('Some files were ignored. Only PDF documents are supported.');
    }

    if (validPdfs.length > 0) {
      setFiles((prev) => [...prev, ...validPdfs]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
    // reset input so the same file can be re-selected if deleted
    e.target.value = '';
  };

  const removeFile = (indexToRemove) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSubmittingRef.current || isAnalyzing) {
      return;
    }
    if (!question.trim()) {
      setErrorMsg('Please specify a research question or inquiry.');
      return;
    }
    if (files.length === 0) {
      setErrorMsg('Please upload at least one PDF research paper to analyze.');
      return;
    }
    isSubmittingRef.current = true;
    setErrorMsg('');
    onStartAnalysis(question.trim(), files);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', width: '100%', padding: '40px 24px' }}>
      {/* Intro Header */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '9999px',
          background: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          color: 'var(--accent-indigo)',
          fontSize: '0.8rem',
          fontWeight: '600',
          marginBottom: '16px'
        }}>
          <Sparkles size={14} />
          Multi-Agent Evidence-Grounded Synthesis
        </div>
        <h2 style={{ fontSize: '2rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#F8FAFC' }}>
          Research Paper Analyzer
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.98rem', maxWidth: '600px', margin: '8px auto 0' }}>
          Extract, verify, and cross-examine findings across complex scientific papers using a 5-stage agentic reasoning pipeline.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Research Question Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <label 
            htmlFor="research-question"
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              marginBottom: '10px', 
              fontWeight: '600', 
              fontSize: '0.92rem', 
              color: 'var(--text-main)' 
            }}
          >
            <span>Research Question or Objective</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 'normal' }}>
              {question.length} characters
            </span>
          </label>
          <textarea
            id="research-question"
            rows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., What are the core architectural mechanisms in these papers, and what are their proven empirical performance trade-offs?"
            style={{
              width: '100%',
              padding: '14px 16px',
              borderRadius: '10px',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: '#FFFFFF',
              fontSize: '0.95rem',
              lineHeight: '1.5',
              fontFamily: 'inherit',
              resize: 'vertical',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--accent-indigo)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border-subtle)')}
          />

          {/* Quick Suggestions */}
          <div style={{ marginTop: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.76rem', color: 'var(--text-dim)', marginBottom: '8px' }}>
              <Lightbulb size={13} color="var(--accent-violet)" />
              <span>Suggested prompts:</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {SUGGESTIONS.map((item, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => setQuestion(item)}
                  style={{
                    padding: '5px 12px',
                    borderRadius: '6px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-muted)',
                    fontSize: '0.76rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#FFFFFF';
                    e.currentTarget.style.borderColor = 'var(--accent-indigo)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = 'var(--text-muted)';
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* PDF Upload Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ fontWeight: '600', fontSize: '0.92rem', color: 'var(--text-main)' }}>
              Source Research Papers (PDF)
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              {files.length} paper{files.length === 1 ? '' : 's'} staged
            </div>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: isDragging ? '2px dashed var(--accent-violet)' : '2px dashed rgba(255, 255, 255, 0.12)',
              borderRadius: '12px',
              padding: '36px 20px',
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragging ? 'rgba(139, 92, 246, 0.08)' : 'rgba(0, 0, 0, 0.15)',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,application/pdf"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
            />
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.15)',
              color: 'var(--accent-indigo)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 12px'
            }}>
              <UploadCloud size={24} />
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#F8FAFC', marginBottom: '4px' }}>
              Drag & drop PDFs here, or click to browse
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Multi-file upload supported. PyMuPDF section parsing and vector indexing occur automatically.
            </div>
          </div>

          {/* Staged Files List */}
          {files.length > 0 && (
            <div style={{ marginTop: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-muted)' }}>
                Staged for Analysis:
              </div>
              {files.map((file, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
                    <FileText size={18} color="var(--accent-violet)" style={{ flexShrink: 0 }} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        color: 'var(--text-main)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {file.name}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                        {formatFileSize(file.size)}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(idx);
                    }}
                    title="Remove paper"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-dim)',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'color 0.15s ease'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#F87171')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#F87171',
            fontSize: '0.88rem'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Submit Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '14px' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
            {files.length} paper{files.length === 1 ? '' : 's'} selected
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={isAnalyzing || isSubmittingRef.current || files.length === 0 || !question.trim()}
            style={{ minWidth: '180px' }}
          >
            <Sparkles size={18} />
            <span>Analyze Papers</span>
          </button>
        </div>
      </form>
    </div>
  );
}
