import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, Package, HelpCircle, Tag, RotateCcw, Clock, ShieldCheck, ChevronDown, ChevronRight, FileText } from 'lucide-react';

export default function Chat({ messages, onSendMessage, loading }) {
  const [input, setInput] = useState('');
  const endOfMessagesRef = useRef(null);

  // Auto-scroll to bottom when messages change
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
    { icon: <Package size={18} className="text-primary" />, title: 'Order Status', text: 'Where is my order ORD-1025?' },
    { icon: <RotateCcw size={18} className="text-primary" />, title: 'Returns', text: 'How do I return a product?' },
    { icon: <ShieldCheck size={18} className="text-primary" />, title: 'Refund Policy', text: 'What is your refund policy?' },
    { icon: <Tag size={18} className="text-primary" />, title: 'Search Products', text: 'Show me laptops under 60000' },
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
                I can help you track orders, process returns, answer policy questions, and find the perfect product.
              </p>
            </div>
            <div className="suggestion-grid">
              {suggestions.map((s, i) => (
                <div key={i} className="suggestion-card" onClick={() => onSendMessage(s.text)}>
                  <div style={{ color: 'var(--primary)', marginBottom: '8px' }}>{s.icon}</div>
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

      <div className="input-area">
        <form className="input-container" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-textarea"
            placeholder="Type your message here..."
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
        
        {/* Render tool trace if available */}
        {!isUser && msg.metadata_?.tool_calls?.length > 0 && (
          <ToolTrace calls={msg.metadata_.tool_calls} />
        )}
        
        {/* Render sources if available */}
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
  
  return (
    <div className="tool-trace">
      <button className="tool-trace-header" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {calls.length} Tool Call{calls.length > 1 ? 's' : ''} Executed
      </button>
      {expanded && (
        <div className="tool-trace-body">
          {calls.map((call, i) => (
            <div key={i} className="tool-call-item">
              <div className="tool-call-name">🛠️ {call.tool}</div>
              <div className="tool-call-detail">Args: {JSON.stringify(call.input)}</div>
              {/* <div className="tool-call-detail text-muted">Returns: {call.output?.substring(0, 50)}...</div> */}
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
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
