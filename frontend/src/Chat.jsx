import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Send, Bot, Package, HelpCircle, Tag, RotateCcw, Clock,
  ShieldCheck, ChevronDown, ChevronRight, FileText, CheckCircle,
  XCircle, AlertTriangle, Zap
} from 'lucide-react';

export default function Chat({ messages, onSendMessage, loading, hitlState, onConfirm, onCancel }) {
  const [input, setInput] = useState('');
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input);
    setInput('');
  };

  const suggestions = [
    { icon: <Package size={18} />, title: 'Order Status', text: 'Where is my order ORD-1025?' },
    { icon: <RotateCcw size={18} />, title: 'Returns', text: 'How do I return a product?' },
    { icon: <ShieldCheck size={18} />, title: 'Refund Policy', text: 'What is your refund policy?' },
    { icon: <Tag size={18} />, title: 'Search Products', text: 'Show me laptops under 60000' },
  ];

  return (
    <div className="main-content">
      <div className="chat-header">
        <div className="chat-header-title">AgentOps Assistant</div>
        <div className="status-badge">
          <div className="status-dot"></div>
          Online
        </div>
      </div>

      <div className="messages-area">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-icon">
              <Bot color="white" size={40} />
            </div>
            <div>
              <h2 className="welcome-title">How can I help you today?</h2>
              <p className="welcome-sub">
                I can help you track orders, process returns, answer policy questions, and find products.
              </p>
            </div>
            <div className="suggestion-grid">
              {suggestions.map((s, i) => (
                <div key={i} className="suggestion-card" onClick={() => onSendMessage(s.text)}>
                  <div style={{ color: 'var(--primary)', marginBottom: 8 }}>{s.icon}</div>
                  <div className="suggestion-title">{s.title}</div>
                  <div className="suggestion-text">"{s.text}"</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageRow key={idx} msg={msg} />
          ))
        )}

        {loading && (
          <div className="message-row bot">
            <div className="message-avatar bot"><Bot size={18} /></div>
            <div className="message-content">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* HITL Confirmation Banner */}
      {hitlState?.awaiting && !loading && (
        <div className="hitl-banner">
          <AlertTriangle size={18} color="var(--warning)" />
          <div className="hitl-text">
            <strong>Confirmation Required</strong>
            <span>The agent needs your approval before proceeding.</span>
          </div>
          <div className="hitl-buttons">
            <button className="hitl-confirm" onClick={onConfirm}>
              <CheckCircle size={14} /> Yes, Proceed
            </button>
            <button className="hitl-cancel" onClick={onCancel}>
              <XCircle size={14} /> Cancel
            </button>
          </div>
        </div>
      )}

      <div className="input-area">
        <form className="input-container" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-textarea"
            placeholder={hitlState?.awaiting ? 'Type Yes to confirm or No to cancel...' : 'Type your message here...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || loading}>
            <Send size={18} />
          </button>
        </form>
        <div className="input-hint">
          AgentOps may make mistakes. Verify important policy or pricing information.
        </div>
      </div>
    </div>
  );
}

function MessageRow({ msg }) {
  const isUser = msg.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'bot'}`}>
      <div className={`message-avatar ${isUser ? 'user' : 'bot'}`}>
        {isUser ? 'U' : <Bot size={18} />}
      </div>
      <div className="message-content">
        <div className="message-bubble">
          {isUser ? (
            msg.content
          ) : (
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          )}
        </div>

        {/* Awaiting confirmation badge */}
        {!isUser && msg.metadata_?.awaiting_confirmation && (
          <div className="hitl-pending-badge">
            <AlertTriangle size={12} color="var(--warning)" />
            Waiting for your confirmation
          </div>
        )}

        {/* Enhanced Tool Trace */}
        {!isUser && msg.metadata_?.tool_calls?.length > 0 && (
          <ToolTrace calls={msg.metadata_.tool_calls} />
        )}

        {/* Sources */}
        {!isUser && msg.metadata_?.sources?.length > 0 && (
          <Sources sources={msg.metadata_.sources} />
        )}

        <div className="message-time">
          {new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}

function ToolTrace({ calls }) {
  const [expanded, setExpanded] = useState(false);

  if (!calls || calls.length === 0) return null;

  const toolIcons = {
    get_order_status: '📦',
    get_order_details: '📋',
    get_customer_orders: '🛍️',
    search_products: '🔍',
    search_knowledge_base: '📚',
    create_support_ticket: '🎫',
    calculate: '🧮',
  };

  const toolLabels = {
    get_order_status: 'Checking order status',
    get_order_details: 'Retrieving order details',
    get_customer_orders: 'Loading your orders',
    search_products: 'Searching product catalog',
    search_knowledge_base: 'Searching knowledge base',
    create_support_ticket: 'Creating support ticket',
    calculate: 'Calculating',
  };

  return (
    <div className="tool-trace">
      <button className="tool-trace-header" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Zap size={12} style={{ color: 'var(--warning)' }} />
        {calls.length} Tool Call{calls.length > 1 ? 's' : ''} Executed
      </button>
      {expanded && (
        <div className="tool-trace-body">
          {calls.map((call, i) => (
            <div key={i} className="tool-call-item">
              <div className="tool-call-name">
                <span>{toolIcons[call.tool] || '🛠️'}</span>
                <strong>{toolLabels[call.tool] || call.tool}</strong>
              </div>
              {call.input && Object.keys(call.input).length > 0 && (
                <div className="tool-call-detail">
                  {Object.entries(call.input).map(([k, v]) => (
                    <span key={k} className="tool-arg">
                      <span className="tool-arg-key">{k}</span>: {String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Sources({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-section">
      <div className="sources-label">
        <ShieldCheck size={14} /> Official Sources Cited
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {sources.map((source, i) => (
          <div key={i} className="source-item">
            <FileText size={12} />
            <span>{source.source} &rarr; <strong>{source.section}</strong></span>
          </div>
        ))}
      </div>
    </div>
  );
}
