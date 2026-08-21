import { useState } from 'react';
import { Bot, Plus, MessageSquare, LogOut, Search } from 'lucide-react';

export default function Sidebar({
  user,
  conversations,
  currentConvId,
  onSelectConv,
  onNewChat,
  onLogout,
}) {
  const [search, setSearch] = useState('');

  const filtered = conversations.filter((c) =>
    (c.title || 'New Chat').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <a href="/" className="logo">
          <div className="logo-icon"><Bot size={20} /></div>
          <div>
            <div className="logo-text">AgentOps</div>
            <div className="logo-sub">ShopEase Assistant</div>
          </div>
        </a>
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={16} /> New Chat
        </button>
      </div>

      <div className="sidebar-section">
        {conversations.length > 0 && (
          <div style={{ marginBottom: 12, padding: '0 8px' }}>
            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: 8, top: 8, color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search chats..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '6px 12px 6px 28px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                  fontSize: '12px',
                  outline: 'none',
                }}
              />
            </div>
          </div>
        )}

        <div className="sidebar-section-label">Recent Chats</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {filtered.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '8px', textAlign: 'center' }}>
              No chats found.
            </div>
          ) : (
            filtered.map((conv) => (
              <div
                key={conv.id}
                className={`conv-item ${currentConvId === conv.id ? 'active' : ''}`}
                onClick={() => onSelectConv(conv.id)}
              >
                <MessageSquare size={16} />
                <span className="conv-item-text">
                  {conv.title || 'New Conversation'}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="user-badge" onClick={onLogout} title="Click to logout">
          <div className="avatar">
            {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="user-info">
            <div className="user-name">{user.full_name}</div>
            <div className="user-email">{user.email}</div>
          </div>
          <LogOut size={16} color="var(--text-muted)" />
        </div>
      </div>
    </div>
  );
}
