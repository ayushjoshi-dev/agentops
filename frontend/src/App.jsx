import { useState, useEffect } from 'react';
import Auth from './Auth';
import Sidebar from './Sidebar';
import Chat from './Chat';
import { listConversations, getConversationMessages, sendMessage } from './api';

export default function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load conversations when user logs in
  useEffect(() => {
    if (user && user.id !== 'demo') {
      listConversations().then(setConversations).catch(console.error);
    }
  }, [user]);

  // Load messages when conversation changes
  useEffect(() => {
    if (currentConvId) {
      if (user && user.id !== 'demo') {
        getConversationMessages(currentConvId)
          .then(setMessages)
          .catch(console.error);
      } else {
        // In demo mode, we don't persist multiple conversations in the frontend state well
        // but we can load from the backend if we want. For simplicity, we just clear it
        // unless it's the active one.
      }
    } else {
      setMessages([]);
    }
  }, [currentConvId, user]);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('agentops_token');
    setUser(null);
    setConversations([]);
    setCurrentConvId(null);
    setMessages([]);
  };

  const handleNewChat = () => {
    setCurrentConvId(null);
    setMessages([]);
  };

  const handleSelectConv = (id) => {
    setCurrentConvId(id);
  };

  const handleSendMessage = async (text) => {
    // Optimistic UI update for user message
    const tempId = Date.now().toString();
    const newMsg = {
      id: tempId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMsg]);
    setLoading(true);

    try {
      const result = await sendMessage(text, currentConvId);
      
      // Update with the real response
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: result.response,
          created_at: new Date().toISOString(),
          metadata_: {
            tool_calls: result.tool_calls_trace,
            sources: result.sources,
          },
        }
      ]);

      // If this was a new conversation, update the ID and list
      if (!currentConvId && result.conversation_id) {
        setCurrentConvId(result.conversation_id);
        if (user && user.id !== 'demo') {
          listConversations().then(setConversations);
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${err.message || 'Something went wrong.'}`,
          created_at: new Date().toISOString(),
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div className="app-layout">
      <Sidebar
        user={user}
        conversations={conversations}
        currentConvId={currentConvId}
        onSelectConv={handleSelectConv}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
      />
      <Chat
        messages={messages}
        onSendMessage={handleSendMessage}
        loading={loading}
      />
    </div>
  );
}
