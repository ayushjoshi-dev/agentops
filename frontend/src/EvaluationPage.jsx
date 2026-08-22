import { useState, useEffect } from 'react';
import { getLatestEvaluation, triggerEvaluation } from './api';
import { BarChart2, CheckCircle, XCircle, Clock, Shield, Zap, Target, PlayCircle, RefreshCw, AlertTriangle } from 'lucide-react';

export default function EvaluationPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    try {
      const data = await getLatestEvaluation();
      setReport(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  const handleRunEvaluation = async () => {
    setRunning(true);
    try {
      await triggerEvaluation(10); // Run first 10 cases for speed
      // Poll for results after a delay
      setTimeout(async () => {
        await fetchReport();
        setRunning(false);
      }, 8000);
    } catch (e) {
      setError(e.message);
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="eval-loading">
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
        <p style={{ marginTop: 16, color: 'var(--text-secondary)' }}>Loading evaluation results...</p>
      </div>
    );
  }

  const metrics = report?.metrics || null;
  const results = report?.results || [];

  return (
    <div className="eval-page">
      <div className="eval-header">
        <div>
          <h1 className="eval-title">
            <BarChart2 size={28} style={{ display: 'inline', marginRight: 12, color: 'var(--primary)' }} />
            AI Evaluation Dashboard
          </h1>
          <p className="eval-subtitle">
            Objective metrics measuring agent quality, tool selection accuracy, and RAG performance.
            {report?.timestamp && (
              <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: 12 }}>
                Last run: {new Date(report.timestamp).toLocaleString()}
              </span>
            )}
          </p>
        </div>
        <button
          className="eval-run-btn"
          onClick={handleRunEvaluation}
          disabled={running}
        >
          {running ? (
            <><RefreshCw size={16} className="spin" /> Running...</>
          ) : (
            <><PlayCircle size={16} /> Run Evaluation</>
          )}
        </button>
      </div>

      {report?.status === 'no_reports' ? (
        <div className="eval-empty">
          <AlertTriangle size={48} color="var(--warning)" />
          <h3>No Evaluation Run Yet</h3>
          <p>Click "Run Evaluation" to test the agent against 30 real test cases.</p>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
            Note: This requires the Groq API key and calls the live agent.
          </p>
        </div>
      ) : metrics ? (
        <>
          {/* Metric Cards */}
          <div className="eval-metrics-grid">
            <MetricCard
              icon={<Target size={22} />}
              label="Tool Selection Accuracy"
              value={`${metrics.tool_selection_accuracy}%`}
              color="var(--primary)"
              description="Correct tool called / total expected"
            />
            <MetricCard
              icon={<CheckCircle size={22} />}
              label="Task Success Rate"
              value={`${metrics.task_success_rate}%`}
              color="var(--success)"
              description="Valid responses / total cases"
            />
            <MetricCard
              icon={<Zap size={22} />}
              label="RAG Trigger Rate"
              value={`${metrics.rag_trigger_rate}%`}
              color="var(--secondary)"
              description="RAG called when expected"
            />
            <MetricCard
              icon={<Shield size={22} />}
              label="Security Refusal Rate"
              value={`${metrics.security_refusal_rate}%`}
              color="#059669"
              description="Injection attempts correctly refused"
            />
            <MetricCard
              icon={<Clock size={22} />}
              label="Avg Latency"
              value={`${(metrics.average_latency_ms / 1000).toFixed(1)}s`}
              color="var(--warning)"
              description="Average response time"
            />
            <MetricCard
              icon={<XCircle size={22} />}
              label="Error Rate"
              value={`${metrics.error_rate}%`}
              color="var(--error)"
              description="Failed agent runs / total"
            />
          </div>

          {/* Summary */}
          <div className="eval-summary-bar">
            <div className="eval-summary-stat">
              <span className="eval-summary-num">{metrics.total_cases}</span>
              <span className="eval-summary-label">Total Cases</span>
            </div>
            <div className="eval-summary-stat">
              <span className="eval-summary-num" style={{ color: 'var(--success)' }}>{metrics.passed_cases}</span>
              <span className="eval-summary-label">Passed</span>
            </div>
            <div className="eval-summary-stat">
              <span className="eval-summary-num" style={{ color: 'var(--error)' }}>{metrics.failed_cases}</span>
              <span className="eval-summary-label">Failed</span>
            </div>
            <div className="eval-summary-stat">
              <span className="eval-summary-num" style={{ color: 'var(--text-muted)', fontSize: 13 }}>LLM-as-judge</span>
              <span className="eval-summary-label">Groundedness</span>
            </div>
          </div>

          {/* Category breakdown */}
          {metrics.categories && (
            <div className="eval-categories">
              <h3 className="eval-section-title">Test Case Categories</h3>
              <div className="eval-cat-grid">
                {Object.entries(metrics.categories).map(([cat, count]) => (
                  <div key={cat} className="eval-cat-item">
                    <span className="eval-cat-name">{cat.replace('_', ' ')}</span>
                    <span className="eval-cat-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Test results table */}
          {results.length > 0 && (
            <div className="eval-results">
              <h3 className="eval-section-title">Test Case Results</h3>
              <div className="eval-table-wrapper">
                <table className="eval-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Question</th>
                      <th>Expected Tools</th>
                      <th>Called Tools</th>
                      <th>Status</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r) => {
                      const pass = r.success;
                      const toolMatch = r.expected_tools?.length === 0 ||
                        r.expected_tools?.some(t => r.tools_called?.includes(t));
                      return (
                        <tr key={r.id} className={pass ? 'row-pass' : 'row-fail'}>
                          <td><code className="eval-id">{r.id}</code></td>
                          <td className="eval-question">{r.question}</td>
                          <td>
                            {(r.expected_tools || []).map(t => (
                              <span key={t} className="eval-tag expected">{t}</span>
                            ))}
                          </td>
                          <td>
                            {(r.tools_called || []).map(t => (
                              <span key={t} className={`eval-tag ${r.expected_tools?.includes(t) ? 'match' : 'other'}`}>
                                {t}
                              </span>
                            ))}
                          </td>
                          <td>
                            {pass
                              ? <span className="eval-status pass"><CheckCircle size={14} /> Pass</span>
                              : <span className="eval-status fail"><XCircle size={14} /> Fail</span>
                            }
                          </td>
                          <td className="eval-latency">{r.latency_ms ? `${(r.latency_ms/1000).toFixed(1)}s` : '-'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : null}

      <div className="eval-note">
        <strong>Note on Groundedness:</strong> Groundedness requires an LLM-as-judge to evaluate whether responses are 
        supported by retrieved documents. This requires a separate LLM call per test case and is labeled accordingly
        rather than auto-calculated.
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, color, description }) {
  return (
    <div className="eval-metric-card">
      <div className="eval-metric-icon" style={{ color }}>
        {icon}
      </div>
      <div className="eval-metric-value" style={{ color }}>{value}</div>
      <div className="eval-metric-label">{label}</div>
      <div className="eval-metric-desc">{description}</div>
    </div>
  );
}
