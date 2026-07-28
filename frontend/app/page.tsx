'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const EXAMPLE_QUERIES = [
  'What is the core architecture of ResNet?',
  'What is the passenger demand forecast for 2050?',
  'Explain the software architecture patterns described.',
  'What does the AWS architecture standards document say?',
  'Summarize the key findings in the uploaded report.',
];

const SOURCE_PILLS = [
  { key: 'all',    label: 'All Sources',  color: '#6366f1' },
  { key: 'pdf',    label: 'PDF',          color: '#f87171' },
  { key: 'github', label: 'GitHub',       color: '#c084fc' },
  { key: 'docx',   label: 'Word',         color: '#60a5fa' },
  { key: 'pptx',   label: 'PowerPoint',   color: '#fb923c' },
  { key: 'xlsx',   label: 'Excel',        color: '#34d399' },
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState('all');
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    const p = new URLSearchParams({ q: query.trim() });
    if (selected !== 'all') p.set('type', selected);
    router.push(`/search?${p.toString()}`);
  };

  return (
    <main className="hero">
      <div className="hero-eyebrow animate-in">
        <span className="hero-eyebrow-dot" />
        AI-Powered Enterprise Search
      </div>

      <h1 className="animate-in animate-delay-1">
        Search everything<br />
        <span className="gradient-text">across your knowledge base</span>
      </h1>

      <p className="hero-desc animate-in animate-delay-2">
        Zephyr searches across PDFs, Word documents, PowerPoints, Excel sheets,
        and GitHub repositories using semantic AI retrieval.
      </p>

      <form className="search-box animate-in animate-delay-3" onSubmit={handleSearch}>
        <div className="search-input-wrap">
          <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <circle cx="11" cy="11" r="8" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
          </svg>
          <input
            ref={inputRef}
            id="main-search-input"
            type="text"
            className="search-input"
            placeholder="Ask anything about your documents…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <button
            id="main-search-btn"
            type="submit"
            className="search-btn"
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <span className="spinner" />
            ) : (
              <>
                <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 12h14" />
                </svg>
                Search
              </>
            )}
          </button>
        </div>

        <div className="filter-row">
          {SOURCE_PILLS.map(p => (
            <button
              key={p.key}
              id={`filter-${p.key}`}
              type="button"
              className={`filter-pill${selected === p.key ? ' active' : ''}`}
              onClick={() => setSelected(p.key)}
            >
              <span className="pill-dot" style={{ background: p.color }} />
              {p.label}
            </button>
          ))}
        </div>
      </form>

      <div className="example-queries animate-in animate-delay-3">
        <div className="example-queries-label">Try asking</div>
        <div className="example-chips">
          {EXAMPLE_QUERIES.map((q, i) => (
            <button
              key={i}
              id={`example-query-${i}`}
              type="button"
              className="example-chip"
              onClick={() => setQuery(q)}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="stats-row animate-in animate-delay-3">
        {[
          { value: '5+', label: 'Source Types' },
          { value: 'RAG', label: 'Retrieval Method' },
          { value: 'pgvector', label: 'Vector Store' },
          { value: 'Groq', label: 'LLM Provider' },
        ].map(s => (
          <div key={s.label} className="stat-item">
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
