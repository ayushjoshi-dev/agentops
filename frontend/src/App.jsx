import { useState, useEffect } from 'react';
import Auth from './Auth';
import Sidebar from './Sidebar';
import Chat from './Chat';
import EvaluationPage from './EvaluationPage';
import { listConversations, getConversationMessages, sendMessage } from './api';

export default function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activePage, setActivePage] = useState('chat'); // 'chat' | 'evaluation'
  // HITL state: persisted across messages for the same conversation
  const [hitlState, setHitlState] = useState({ awaiting: false, pending: null });

  useEffect(() => {
    if (user && user.id !== 'demo') {
      listConversations().then(setConversations).catch(console.error);
    }
  }, [user]);

  useEffect(() => {
    if (currentConvId) {
      if (user && user.id !== 'demo') {
        getConversationMessages(currentConvId)
          .then(setMessages)
          .catch(console.error);
      }
    } else {
      setMessages([]);
    }
  }, [currentConvId, user]);

  const handleLogin = (userData) => { setUser(userData); };

  const handleLogout = () => {
    localStorage.removeItem('agentops_token');
    setUser(null);
    setConversations([]);
    setCurrentConvId(null);
    setMessages([]);
    setHitlState({ awaiting: false, pending: null });
  };

  const handleNewChat = () => {
    setCurrentConvId(null);
    setMessages([]);
    setHitlState({ awaiting: false, pending: null });
  };

  const handleSelectConv = (id) => {
    setCurrentConvId(id);
    setHitlState({ awaiting: false, pending: null });
  };

  const handleSendMessage = async (text) => {
    const newMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMsg]);
    setLoading(true);

    try {
      const result = await sendMessage(
        text,
        currentConvId,
        hitlState.pending,
        hitlState.awaiting
      );

      // Update HITL state from response
      setHitlState({
        awaiting: result.awaiting_confirmation || false,
        pending: result.pending_action || null,
      });

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
            awaiting_confirmation: result.awaiting_confirmation,
            pending_action: result.pending_action,
          },
        }
      ]);

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

  const handleConfirm = () => handleSendMessage('Yes, please proceed.');
  const handleCancel = () => {
    setHitlState({ awaiting: false, pending: null });
    handleSendMessage('No, cancel that.');
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
        activePage={activePage}
        onPageChange={setActivePage}
      />
      {activePage === 'evaluation' ? (
        <EvaluationPage />
      ) : (
        <Chat
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={loading}
          hitlState={hitlState}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
}
