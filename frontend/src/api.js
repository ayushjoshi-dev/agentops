// AgentOps — API Client
// Centralizes all backend calls with auth token injection

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function getToken() {
  return localStorage.getItem('agentops_token');
}

function authHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(path, options = {}) {
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: authHeaders(),
  });

  if (resp.status === 401) {
    localStorage.removeItem('agentops_token');
    window.location.href = '/';
    return null;
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }

  if (resp.status === 204) return null;
  return resp.json();
}

// ── Auth ──────────────────────────────────────────────────

export async function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email, full_name, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, full_name, password }),
  });
}

export async function getMe() {
  return request('/auth/me');
}

// ── Chat ──────────────────────────────────────────────────

export async function sendMessage(message, conversation_id = null, pending_action = null, awaiting_confirmation = false) {
  const token = getToken();
  const body = { message, conversation_id, pending_action, awaiting_confirmation };
  if (token) {
    return request('/chat', { method: 'POST', body: JSON.stringify(body) });
  } else {
    return request('/chat/demo', { method: 'POST', body: JSON.stringify(body) });
  }
}

// ── Conversations ─────────────────────────────────────────

export async function listConversations() {
  return request('/conversations');
}

export async function getConversationMessages(conversation_id) {
  return request(`/conversations/${conversation_id}/messages`);
}

export async function deleteConversation(conversation_id) {
  return request(`/conversations/${conversation_id}`, { method: 'DELETE' });
}

// ── Orders ────────────────────────────────────────────────

export async function listOrders() {
  return request('/orders');
}

// ── Evaluation ────────────────────────────────────────────

export async function getLatestEvaluation() {
  return request('/evaluation/latest');
}

export async function triggerEvaluation(limit = null) {
  const params = limit ? `?limit=${limit}` : '';
  return request(`/evaluation/run${params}`, { method: 'POST' });
}

export async function getEvaluationDataset() {
  return request('/evaluation/dataset');
}

// ── Traces ────────────────────────────────────────────────

export async function listTraces(limit = 20) {
  return request(`/traces?limit=${limit}`);
}

export async function getTrace(run_id) {
  return request(`/traces/${run_id}`);
}

// ── Health ────────────────────────────────────────────────

export async function healthCheck() {
  return request('/health');
}
