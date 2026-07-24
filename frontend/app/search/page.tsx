'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SearchResult {
  chunk_text: string;
  chunk_title: string | null;
  source_name: string | null;
  source_type: string | null;
  score: number;
  metadata: Record<string, unknown>;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  answer: string | null;
}

const SOURCE_CONFIG: Record<string, { color: string; label: string; accent: string }> = {
  pdf:     { color: 'var(--col-pdf)',    label: 'PDF',        accent: 'var(--col-pdf-bg)' },
  github:  { color: 'var(--col-github)', label: 'GitHub',     accent: 'var(--col-github-bg)' },
  docx:    { color: 'var(--col-docx)',   label: 'Word',       accent: 'var(--col-docx-bg)' },
  pptx:    { color: 'var(--col-pptx)',   label: 'PowerPoint', accent: 'var(--col-pptx-bg)' },
  xlsx:    { color: 'var(--col-xlsx)',   label: 'Excel',      accent: 'var(--col-xlsx-bg)' },
};

const SOURCE_FILTERS = ['all', 'pdf', 'github', 'docx', 'pptx', 'xlsx'];

const PILL_COLORS: Record<string, string> = {
  all:    '#6366f1',
  pdf:    '#f87171',
  github: '#c084fc',
  docx:   '#60a5fa',
  pptx:   '#fb923c',
  xlsx:   '#34d399',
};

// SVG Icons (no emoji)
function FileIcon({ type }: { type: string }) {
  const color = SOURCE_CONFIG[type]?.color || '#6366f1';
  if (type === 'github') return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ color }}>
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
  return (
    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} style={{ color }}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 21H17a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );
}

function getMetaItems(result: SearchResult): { label: string; value: string }[] {
  const items: { label: string; value: string }[] = [];
  const m = result.metadata || {};

  if (m.page_number) items.push({ label: 'Page', value: String(m.page_number) });
  if (m.file_name)   items.push({ label: 'File', value: String(m.file_name) });
  if (m.file_path)   items.push({ label: 'Path', value: String(m.file_path).split('/').pop() || String(m.file_path) });
  if (m.language)    items.push({ label: 'Lang', value: String(m.language) });
  if (m.sheet_name)  items.push({ label: 'Sheet', value: String(m.sheet_name) });

  return items;
}

function ResultCard({ result, index }: { result: SearchResult; index: number }) {
  const type = result.source_type || 'pdf';
  const cfg = SOURCE_CONFIG[type] || { color: '#6366f1', label: type.toUpperCase(), accent: 'rgba(99,102,241,0.1)' };
  const metaItems = getMetaItems(result);
  const scorePercent = Math.min(100, Math.max(0, ((result.score + 10) / 10) * 100));
  const isCode = type === 'github';
  const textPreview = result.chunk_text?.slice(0, 500) || '';

  return (
    <div
      className="result-card animate-in"
      id={`result-card-${index}`}
      style={{
        animationDelay: `${index * 0.04}s`,
        '--card-accent': cfg.color,
      } as React.CSSProperties}
    >
      <style>{`.result-card[style*="--card-accent: ${cfg.color}"]::before { background: ${cfg.color}; }`}</style>

      <div className="result-card-header">
        <div className="result-title">
          {result.chunk_title || result.source_name || 'Untitled'}
        </div>
        <span
          className="type-badge"
          style={{ color: cfg.color, borderColor: cfg.color, background: cfg.accent }}
        >
          <FileIcon type={type} />
          {cfg.label}
        </span>
      </div>

      <div className="result-source">
        <svg width="11" height="11" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 7l9 6 9-6" />
        </svg>
        {result.source_name}
      </div>

      {isCode ? (
        <pre className="code-preview">{textPreview}</pre>
      ) : (
        <p className="result-text">{textPreview}</p>
      )}

      <div className="result-meta-row">
        {metaItems.map((item, i) => (
          <span key={i} className="result-meta-item">
            <span style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{item.label}</span>
            <span style={{ color: 'var(--text-secondary)' }}>{item.value}</span>
          </span>
        ))}

        <div className="relevance">
          <div className="relevance-bar-track">
            <div className="relevance-bar-fill" style={{ width: `${scorePercent}%` }} />
          </div>
          <span className="relevance-text">{scorePercent.toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

function SearchPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const initialQuery = params.get('q') || '';
  const initialType = params.get('type') || 'all';

  const [query, setQuery] = useState(initialQuery);
  const [selectedType, setSelectedType] = useState(initialType);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doSearch = async (q: string, type: string) => {
    if (!q.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { query: q, top_k: 8 };
      if (type !== 'all') body.source_type = type;

      const res = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const json: SearchResponse = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed. Is the backend running?');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) doSearch(initialQuery, initialType);
  }, [initialQuery, initialType]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const p = new URLSearchParams({ q: query.trim() });
    if (selectedType !== 'all') p.set('type', selectedType);
    router.push(`/search?${p.toString()}`);
    doSearch(query.trim(), selectedType);
  };

  return (
    <div className="results-page">
      <div className="results-header">
        <form className="results-bar" onSubmit={handleSearch}>
          <div className="search-input-wrap" style={{ flex: 1 }}>
            <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <circle cx="11" cy="11" r="8" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
            </svg>
            <input
              id="results-search-input"
              type="text"
              className="search-input"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search your knowledge base…"
            />
            <button id="results-search-btn" type="submit" className="search-btn" disabled={isLoading || !query.trim()}>
              {isLoading ? <span className="spinner" /> : 'Search'}
            </button>
          </div>
        </form>

        <div className="filter-row" style={{ justifyContent: 'flex-start', marginBottom: 16 }}>
          {SOURCE_FILTERS.map(t => (
            <button
              key={t}
              id={`filter-${t}`}
              type="button"
              className={`filter-pill${selectedType === t ? ' active' : ''}`}
              onClick={() => {
                setSelectedType(t);
                if (query.trim()) doSearch(query.trim(), t);
              }}
            >
              <span className="pill-dot" style={{ background: PILL_COLORS[t] || '#6366f1' }} />
              {t === 'all' ? 'All Sources' : SOURCE_CONFIG[t]?.label || t}
            </button>
          ))}
        </div>

        {data && !isLoading && (
          <div className="results-meta">
            <div className="results-count">
              <strong>{data.results.length}</strong> result{data.results.length !== 1 ? 's' : ''} for &ldquo;<strong>{data.query}</strong>&rdquo;
            </div>
          </div>
        )}
      </div>

      <div className="results-list">
        {isLoading && (
          <div className="loading-state">
            <div className="loading-dots"><span /><span /><span /></div>
            <p>Searching across all sources…</p>
          </div>
        )}

        {!isLoading && error && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="22" height="22" fill="none" stroke="var(--error)" viewBox="0 0 24 24" strokeWidth={2}>
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h3>Search Failed</h3>
            <p>{error}</p>
          </div>
        )}

        {!isLoading && !error && data?.answer && data.results.length > 0 && (
          <div className="answer-card animate-in">
            <div className="answer-header">
              <svg width="14" height="14" fill="none" stroke="var(--accent-light)" viewBox="0 0 24 24" strokeWidth={2}>
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span className="answer-label">AI Answer</span>
            </div>
            <p className="answer-text">{data.answer}</p>
          </div>
        )}

        {!isLoading && !error && data?.results.map((result, i) => (
          <ResultCard key={i} result={result} index={i} />
        ))}

        {!isLoading && !error && data && data.results.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="22" height="22" fill="none" stroke="var(--text-muted)" viewBox="0 0 24 24" strokeWidth={2}>
                <circle cx="11" cy="11" r="8" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
              </svg>
            </div>
            <h3>No results found</h3>
            <p>Try a different query or upload more documents to your knowledge base.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="loading-state" style={{ minHeight: '80vh' }}>
        <div className="loading-dots"><span /><span /><span /></div>
      </div>
    }>
      <SearchPageInner />
    </Suspense>
  );
}
