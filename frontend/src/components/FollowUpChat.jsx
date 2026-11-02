import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Sparkles, 
  Trash2, 
  BookOpen, 
  Hash, 
  HelpCircle,
  FileText
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

const QUICK_QUESTIONS = [
  "What specific baseline models were evaluated against?",
  "Explain the core limitations and assumptions mentioned.",
  "What loss functions or optimization objectives were utilized?",
  "Are there statistical significance tests reported for the benchmark numbers?"
];

export default function FollowUpChat({ finalReport, evidence }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'I have ingested your analyzed papers and findings. Ask any deep follow-up questions about the methodology, claims, data, or limitations.',
      sources: []
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  const handleSend = async (questionToSend) => {
    const query = (questionToSend || inputQuestion).trim();
    if (!query || isSending) return;

    setErrorMsg('');
    setInputQuestion('');

    const newMessages = [...messages, { role: 'user', content: query }];
    setMessages(newMessages);
    setIsSending(true);

    try {
      // Build previous dialogue history for context
      const chatHistory = newMessages.slice(1, -1).map((m) => ({
        role: m.role,
        content: m.content
      }));

      const response = await sendChatMessage({
        question: query,
        context: finalReport || '',
        evidence: evidence || [],
        history: chatHistory
      });

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer || 'No response generated.',
          sources: response.sources || []
        }
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setErrorMsg(err.message || 'Failed to get answer.');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ **Error communicating with backend**: ${err.message || 'Please check your connection.'}`,
          sources: []
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Conversation cleared. What else would you like to explore regarding these papers?',
        sources: []
      }
    ]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '680px', gap: '14px' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#F8FAFC' }}>
            Interactive Literature Dialogue
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            Evidence-grounded conversational interrogation across parsed papers.
          </p>
        </div>
        <button
          onClick={handleClearHistory}
          className="btn-secondary"
          style={{ padding: '6px 12px', fontSize: '0.78rem' }}
          title="Clear chat history"
        >
          <Trash2 size={13} />
          <span>Clear History</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div
        className="glass-panel"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start',
                flexDirection: isUser ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar */}
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: isUser
                    ? 'linear-gradient(135deg, var(--accent-blue), var(--accent-indigo))'
                    : 'linear-gradient(135deg, var(--accent-indigo), var(--accent-violet))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  flexShrink: 0,
                  boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
                }}
              >
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>

              {/* Message Bubble */}
              <div
                style={{
                  maxWidth: '78%',
                  padding: '14px 18px',
                  borderRadius: '12px',
                  background: isUser ? 'var(--accent-indigo)' : 'var(--bg-card-hover)',
                  border: isUser ? 'none' : '1px solid var(--border-subtle)',
                  color: '#F8FAFC',
                  fontSize: '0.92rem',
                  lineHeight: '1.6',
                }}
              >
                {isUser ? (
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                ) : (
                  <div className="markdown-body">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}

                {/* Sources chip list */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{
                    marginTop: '12px',
                    paddingTop: '10px',
                    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: '600', textTransform: 'uppercase' }}>
                      Cited Sources ({msg.sources.length}):
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {msg.sources.map((src, sIdx) => {
                        const chunk = src.chunk || src;
                        return (
                          <div
                            key={sIdx}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              background: 'rgba(0,0,0,0.3)',
                              border: '1px solid var(--border-subtle)',
                              fontSize: '0.72rem',
                              color: 'var(--text-muted)'
                            }}
                          >
                            <FileText size={12} color="var(--accent-violet)" />
                            <span style={{ fontWeight: '500' }}>{chunk.paper_title || 'Paper'}</span>
                            {chunk.page_number && <span>(p.{chunk.page_number})</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isSending && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--accent-indigo), var(--accent-violet))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
            }}>
              <Bot size={16} />
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 16px',
              borderRadius: '12px',
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              fontSize: '0.85rem'
            }}>
              <Loader2 size={16} className="spin-slow" color="var(--accent-indigo)" />
              <span>Synthesizing grounded answer from indexed literature...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto', paddingBottom: '4px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', flexShrink: 0 }}>
          Follow-up suggestions:
        </span>
        {QUICK_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={isSending}
            style={{
              whiteSpace: 'nowrap',
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              cursor: isSending ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s'
            }}
            onMouseEnter={(e) => {
              if (!isSending) {
                e.currentTarget.style.color = '#FFFFFF';
                e.currentTarget.style.borderColor = 'var(--accent-indigo)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isSending) {
                e.currentTarget.style.color = 'var(--text-muted)';
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
              }
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div style={{ display: 'flex', gap: '10px', position: 'relative' }}>
        <textarea
          rows={2}
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the methodology, data, results, or authors' claims... (Press Enter to send)"
          disabled={isSending}
          style={{
            flex: 1,
            padding: '12px 14px',
            borderRadius: '10px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            color: '#FFFFFF',
            fontSize: '0.9rem',
            lineHeight: '1.4',
            resize: 'none',
            outline: 'none',
            fontFamily: 'inherit'
          }}
          onFocus={(e) => (e.target.style.borderColor = 'var(--accent-indigo)')}
          onBlur={(e) => (e.target.style.borderColor = 'var(--border-subtle)')}
        />
        <button
          onClick={() => handleSend()}
          disabled={isSending || !inputQuestion.trim()}
          className="btn-primary"
          style={{ padding: '0 20px', borderRadius: '10px' }}
          title="Send follow-up question"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
