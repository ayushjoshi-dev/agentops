import { useState, useEffect } from 'react';
import { Bot, Mail, Lock, User, AlertCircle, ArrowRight } from 'lucide-react';
import { login, register, getMe } from './api';

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
  });

  // Check if already logged in on mount
  useEffect(() => {
    const token = localStorage.getItem('agentops_token');
    if (token) {
      getMe()
        .then((user) => onLogin(user))
        .catch(() => localStorage.removeItem('agentops_token'));
    }
  }, [onLogin]);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let data;
      if (isLogin) {
        data = await login(formData.email, formData.password);
      } else {
        data = await register(formData.email, formData.full_name, formData.password);
      }

      if (data && data.access_token) {
        localStorage.setItem('agentops_token', data.access_token);
        const user = await getMe();
        onLogin(user);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoMode = () => {
    // For demo mode, we just bypass auth in the frontend.
    // The API client will use the /chat/demo endpoint if no token is found.
    localStorage.removeItem('agentops_token');
    onLogin({ id: 'demo', email: 'demo@shopease.com', full_name: 'Demo User (Unauthenticated)' });
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon"><Bot size={24} /></div>
          <div>
            <h1 className="auth-title">AgentOps</h1>
            <div className="auth-sub">AI Customer Operations</div>
          </div>
        </div>

        {error && (
          <div className="error-msg">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div style={{ position: 'relative' }}>
                <User size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  name="full_name"
                  className="form-input"
                  style={{ paddingLeft: 36 }}
                  placeholder="John Doe"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
              <input
                type="email"
                name="email"
                className="form-input"
                style={{ paddingLeft: 36 }}
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
              <input
                type="password"
                name="password"
                className="form-input"
                style={{ paddingLeft: 36 }}
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="auth-divider">or</div>

        <button type="button" className="demo-btn" onClick={handleDemoMode}>
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            Continue in Demo Mode <ArrowRight size={16} />
          </span>
        </button>

        <div className="auth-switch">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <a onClick={() => { setIsLogin(!isLogin); setError(null); }}>
            {isLogin ? 'Sign up' : 'Sign in'}
          </a>
        </div>
      </div>
    </div>
  );
}
