import { useState } from 'react';
import { MessageSquare, Plus, Trash2, User, LogOut, BarChart2, ChevronRight } from 'lucide-react';

export default function Sidebar({
  user, conversations, currentConvId, onSelectConv, onNewChat, onLogout,
  activePage, onPageChange
}) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon" style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, width: 36, height: 36 }}>
            <MessageSquare size={18} color="white" />
          </div>
          <div>
            <div className="logo-name">AgentOps</div>
            <div className="logo-tagline">AI Customer Platform</div>
          </div>
        </div>
      </div>

      <div className="sidebar-nav">
        <button
          className={`nav-item ${activePage === 'chat' ? 'active' : ''}`}
          onClick={() => onPageChange('chat')}
        >
          <MessageSquare size={16} />
          Chat
        </button>
        <button
          className={`nav-item ${activePage === 'evaluation' ? 'active' : ''}`}
          onClick={() => onPageChange('evaluation')}
        >
          <BarChart2 size={16} />
          Evaluation
        </button>
      </div>

      {activePage === 'chat' && (
        <>
          <div className="sidebar-section">
            <button className="new-chat-btn" onClick={onNewChat}>
              <Plus size={16} />
              New Chat
            </button>
          </div>

          <div className="conversations-list">
            {conversations.length === 0 ? (
              <div className="no-conversations">No conversations yet</div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`conversation-item ${currentConvId === conv.id ? 'active' : ''}`}
                  onClick={() => onSelectConv(conv.id)}
                >
                  <MessageSquare size={14} className="conv-icon" />
                  <span className="conv-title">{conv.title || 'New Conversation'}</span>
                </div>
              ))
            )}
          </div>
        </>
      )}

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">
            <User size={14} />
          </div>
          <div className="user-details">
            <div className="user-name">{user?.full_name || user?.email || 'User'}</div>
            <div className="user-email">{user?.email || ''}</div>
          </div>
          <button className="logout-btn" onClick={onLogout} title="Logout">
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
