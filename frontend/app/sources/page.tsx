'use client';

import { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Source {
  id: number;
  source_type: string;
  source_name: string;
  source_identifier: string;
  ingested_at: string | null;
  chunk_count: number;
}

const SOURCE_CONFIG: Record<string, { color: string; label: string; bgColor: string }> = {
  pdf:      { color: '#f87171', label: 'PDF',        bgColor: 'rgba(248,113,113,0.10)' },
  github:   { color: '#c084fc', label: 'GitHub',     bgColor: 'rgba(192,132,252,0.10)' },
  docx:     { color: '#60a5fa', label: 'Word',       bgColor: 'rgba(96,165,250,0.10)' },
  pptx:     { color: '#fb923c', label: 'PowerPoint', bgColor: 'rgba(251,146,60,0.10)' },
  xlsx:     { color: '#34d399', label: 'Excel',      bgColor: 'rgba(52,211,153,0.10)' },
};

const FILTER_TYPES = ['all', 'pdf', 'github', 'docx', 'pptx', 'xlsx'];
const PILL_COLORS: Record<string, string> = {
  all: '#6366f1', pdf: '#f87171', github: '#c084fc', docx: '#60a5fa', pptx: '#fb923c', xlsx: '#34d399',
};

// ── Source Icon SVG ───────────────────────────────────────────────────────────

function SourceIcon({ type }: { type: string }) {
  const cfg = SOURCE_CONFIG[type] || { color: '#6366f1', bgColor: 'rgba(99,102,241,0.1)', label: type };

  const icon = type === 'github' ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill={cfg.color}>
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  ) : (
    <svg width="18" height="18" fill="none" stroke={cfg.color} viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 21H17a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );

  return (
    <div className="source-icon" style={{ background: cfg.bgColor }}>
      {icon}
    </div>
  );
}

export default function SourcesPage() {
  const [sources, setSources]     = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [filterType, setFilterType] = useState('all');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmId, setConfirmId]   = useState<number | null>(null);

  const loadSources = async (type?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const url = type && type !== 'all'
        ? `${API_BASE}/sources?source_type=${type}`
        : `${API_BASE}/sources`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSources(data.sources || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadSources(); }, []);

  const handleFilter = (type: string) => {
    setFilterType(type);
    loadSources(type);
  };

  const handleDelete = async (source: Source) => {
    setDeletingId(source.id);
    setConfirmId(null);
    try {
      const res = await fetch(`${API_BASE}/sources/${source.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSources(prev => prev.filter(s => s.id !== source.id));
    } catch (err) {
      console.error('Delete failed:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const totalChunks = sources.reduce((sum, s) => sum + (s.chunk_count || 0), 0);

  const grouped = sources.reduce<Record<string, Source[]>>((acc, s) => {
    if (!acc[s.source_type]) acc[s.source_type] = [];
    acc[s.source_type].push(s);
    return acc;
  }, {});

  return (
    <div className="page-wrapper" style={{ position: 'relative', zIndex: 1 }}>
      <h1 className="page-title animate-in">Data Sources</h1>
      <p className="page-sub animate-in animate-delay-1">
        All ingested data sources. Each source has been parsed, chunked, embedded, and indexed.
      </p>

      {/* Filter */}
      <div className="filter-row animate-in animate-delay-1" style={{ justifyContent: 'flex-start', marginBottom: 24 }}>
        {FILTER_TYPES.map(t => (
          <button
            key={t}
            id={`sources-filter-${t}`}
            type="button"
            className={`filter-pill${filterType === t ? ' active' : ''}`}
            onClick={() => handleFilter(t)}
          >
            <span className="pill-dot" style={{ background: PILL_COLORS[t] || '#6366f1' }} />
            {t === 'all' ? 'All' : SOURCE_CONFIG[t]?.label || t}
          </button>
        ))}
      </div>

      {/* Stats */}
      {!isLoading && !error && (
        <div style={{ display: 'flex', gap: 24, marginBottom: 28, flexWrap: 'wrap' }} className="animate-in">
          <div>
            <span style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.03em' }}>{sources.length}</span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 7 }}>sources indexed</span>
          </div>
          <div>
            <span style={{ fontSize: 24, fontWeight: 700, letterSpacing: '-0.03em' }}>{totalChunks.toLocaleString()}</span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 7 }}>total chunks</span>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="loading-state" style={{ minHeight: 180 }}>
          <div className="loading-dots"><span /><span /><span /></div>
          <p>Loading sources…</p>
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="22" height="22" fill="none" stroke="var(--error)" viewBox="0 0 24 24" strokeWidth={2}>
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3>Failed to load sources</h3>
          <p>{error}</p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !error && sources.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="22" height="22" fill="none" stroke="var(--text-muted)" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
            </svg>
          </div>
          <h3>No sources indexed</h3>
          <p>Upload a document or ingest a GitHub repository to get started.</p>
        </div>
      )}

      {/* Sources by type */}
      {!isLoading && !error && Object.entries(grouped).map(([type, typeSources]) => {
        const cfg = SOURCE_CONFIG[type] || { color: '#6366f1', label: type, bgColor: 'rgba(99,102,241,0.1)' };
        return (
          <div key={type} style={{ marginBottom: 32 }} className="animate-in">
            <div className="section-heading">
              <div className="section-icon" style={{ background: cfg.bgColor }}>
                <SourceIcon type={type} />
              </div>
              <span className="section-label" style={{ color: cfg.color }}>{cfg.label}</span>
              <span className="section-count">{typeSources.length}</span>
            </div>

            <div className="sources-grid">
              {typeSources.map(source => (
                <div key={source.id} className="source-card" id={`source-${source.id}`}>
                  <SourceIcon type={source.source_type} />

                  <div className="source-info">
                    <div className="source-name">{source.source_name}</div>
                    <div className="source-detail" title={source.source_identifier}>
                      {source.source_identifier?.length > 55
                        ? '…' + source.source_identifier.slice(-50)
                        : source.source_identifier}
                    </div>
                    {source.ingested_at && (
                      <div className="source-detail" style={{ marginTop: 2 }}>
                        Indexed {new Date(source.ingested_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </div>
                    )}
                  </div>

                  <div className="source-stats">
                    <div className="chunk-count" style={{ color: cfg.color }}>
                      {(source.chunk_count || 0).toLocaleString()}
                    </div>
                    <div className="chunk-label">chunks</div>
                  </div>

                  {confirmId === source.id ? (
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                      <button
                        id={`confirm-delete-${source.id}`}
                        className="delete-btn"
                        style={{ color: 'var(--error)', borderColor: 'rgba(248,113,113,0.3)' }}
                        onClick={() => handleDelete(source)}
                        disabled={deletingId === source.id}
                      >
                        {deletingId === source.id ? <span className="spinner spinner-sm" /> : 'Confirm'}
                      </button>
                      <button className="delete-btn" onClick={() => setConfirmId(null)}>Cancel</button>
                    </div>
                  ) : (
                    <button
                      id={`delete-source-${source.id}`}
                      className="delete-btn"
                      onClick={() => setConfirmId(source.id)}
                      disabled={deletingId === source.id}
                    >
                      <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <polyline points="3 6 5 6 21 6" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2" />
                      </svg>
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* API Reference */}
      {!isLoading && (
        <>
          <div className="divider" />
          <div className="info-block animate-in">
            <div className="info-block-title">API Endpoints</div>
            {[
              { method: 'POST', url: '/upload',        desc: 'Upload PDF, DOCX, PPTX, or XLSX (multipart/form-data)' },
              { method: 'POST', url: '/ingest/github', desc: '{ "owner": "...", "repo": "..." }' },
              { method: 'POST', url: '/search',        desc: '{ "query": "...", "top_k": 5 }' },
              { method: 'GET',  url: '/sources',       desc: 'List all ingested sources' },
              { method: 'DELETE', url: '/sources/:id', desc: 'Delete a source and all its chunks' },
            ].map(api => (
              <div key={api.url} className="api-row">
                <span className="api-method">{api.method}</span>
                <span className="api-url">{api.url}</span>
                <span className="api-desc">{api.desc}</span>
              </div>
            ))}
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 14 }}>
              API running at <code style={{ color: 'var(--col-xlsx)', fontFamily: 'JetBrains Mono, monospace' }}>{API_BASE}</code>.
              &nbsp;
              <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-light)' }}>
                Open Swagger UI →
              </a>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
