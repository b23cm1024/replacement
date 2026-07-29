'use client';

import { useState, useRef, useCallback, DragEvent, ChangeEvent } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type TabKey = 'document' | 'github';

interface Toast {
  id: number;
  type: 'success' | 'error' | 'loading';
  message: string;
}

const TABS: { key: TabKey; label: string; color: string }[] = [
  { key: 'document', label: 'Upload Document', color: '#6366f1' },
  { key: 'github',   label: 'GitHub Repository', color: '#c084fc' },
];

let toastId = 0;

// ── Utility SVGs ──────────────────────────────────────────────────────────────

function UploadCloudIcon({ color }: { color: string }) {
  return (
    <svg width="40" height="40" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={1.5} style={{ opacity: 0.45 }}>
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
    </svg>
  );
}

function FileDocIcon({ color }: { color: string }) {
  return (
    <svg width="20" height="20" fill="none" stroke={color} viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 21H17a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );
}

function GithubIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill={color}>
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function UploadPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('document');
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (type: Toast['type'], message: string): number => {
    const id = ++toastId;
    setToasts(prev => [...prev, { id, type, message }]);
    if (type !== 'loading') setTimeout(() => removeToast(id), 5500);
    return id;
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const updateToast = (id: number, type: Toast['type'], message: string) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, type, message } : t));
    if (type !== 'loading') setTimeout(() => removeToast(id), 5500);
  };

  return (
    <div className="page-wrapper">
      <h1 className="page-title animate-in">Upload Sources</h1>
      <p className="page-sub animate-in animate-delay-1">
        Upload documents or connect GitHub repositories to make them searchable through the AI pipeline.
      </p>

      <div className="upload-tabs animate-in animate-delay-1">
        {TABS.map(tab => (
          <button
            key={tab.key}
            id={`tab-${tab.key}`}
            type="button"
            className={`upload-tab${activeTab === tab.key ? ' active' : ''}`}
            style={activeTab === tab.key ? { color: tab.color } : {}}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.key === 'github' ? <GithubIcon color={activeTab === tab.key ? tab.color : 'var(--text-muted)'} /> : (
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 21H17a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            )}
            {tab.label}
          </button>
        ))}
      </div>

      <div className="upload-panel animate-in animate-delay-2">
        {activeTab === 'document' && <DocumentPanel addToast={addToast} updateToast={updateToast} />}
        {activeTab === 'github'   && <GitHubPanel   addToast={addToast} updateToast={updateToast} />}
      </div>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <span className="toast-icon">
              {toast.type === 'loading' ? (
                <span className="toast-spinner" />
              ) : toast.type === 'success' ? (
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : (
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              )}
            </span>
            <span className="toast-body">{toast.message}</span>
            <button className="toast-close" onClick={() => removeToast(toast.id)}>×</button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Panel Props ───────────────────────────────────────────────────────────────

interface PanelProps {
  addToast: (type: Toast['type'], msg: string) => number;
  updateToast: (id: number, type: Toast['type'], msg: string) => void;
}

// ── Document Upload Panel ─────────────────────────────────────────────────────

const SUPPORTED_TYPES = [
  { ext: '.pdf',  label: 'PDF',        color: '#f87171' },
  { ext: '.docx', label: 'Word',       color: '#60a5fa' },
  { ext: '.pptx', label: 'PowerPoint', color: '#fb923c' },
  { ext: '.xlsx', label: 'Excel',      color: '#34d399' },
];

const ACCEPT_EXTS = SUPPORTED_TYPES.map(t => t.ext).join(',');

function getFileColor(name: string): string {
  const ext = '.' + name.split('.').pop()?.toLowerCase();
  return SUPPORTED_TYPES.find(t => t.ext === ext)?.color || '#6366f1';
}

function getFileLabel(name: string): string {
  const ext = '.' + name.split('.').pop()?.toLowerCase();
  return SUPPORTED_TYPES.find(t => t.ext === ext)?.label || ext.toUpperCase();
}

function DocumentPanel({ addToast, updateToast }: PanelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const isValidFile = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    return SUPPORTED_TYPES.some(t => t.ext === ext);
  };

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && isValidFile(file)) {
      setSelectedFile(file);
    } else {
      addToast('error', `Unsupported file type. Accepted: ${SUPPORTED_TYPES.map(t => t.ext).join(', ')}`);
    }
  }, [addToast]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    const tid = addToast('loading', `Processing "${selectedFile.name}"…`);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const interval = setInterval(() => {
        setProgress(prev => (prev !== null && prev < 88 ? prev + 7 : prev));
      }, 500);

      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });

      clearInterval(interval);
      setProgress(100);

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      updateToast(tid, 'success', `"${selectedFile.name}" ingested — ${data.chunks_stored} chunks indexed`);
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = '';
    } catch (err) {
      updateToast(tid, 'error', `Upload failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setTimeout(() => setProgress(null), 1000);
    }
  };

  const fileColor = selectedFile ? getFileColor(selectedFile.name) : '#6366f1';

  return (
    <div>
      <div className="panel-header">
        <div className="panel-title">
          <div className="panel-title-icon" style={{ background: 'rgba(99,102,241,0.1)' }}>
            <svg width="16" height="16" fill="none" stroke="var(--accent-light)" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          Document Upload
        </div>
        <p className="panel-desc">
          Upload a document and the AI pipeline will extract, chunk, embed, and index it for semantic search.
          Supported: {SUPPORTED_TYPES.map(t => <span key={t.ext}><code>{t.ext}</code> </span>)}
        </p>
      </div>

      <div
        id="document-dropzone"
        className={`dropzone${isDragging ? ' dragging' : ''}${selectedFile ? ' has-file' : ''}`}
        onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          id="document-file-input"
          type="file"
          accept={ACCEPT_EXTS}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {selectedFile ? (
          <div className="dropzone-selected">
            <div className="dropzone-file-icon" style={{ background: `${fileColor}15` }}>
              <FileDocIcon color={fileColor} />
            </div>
            <div>
              <div className="dropzone-filename">{selectedFile.name}</div>
              <div className="dropzone-filesize">
                {getFileLabel(selectedFile.name)} · {(selectedFile.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <button
              className="dropzone-clear"
              onClick={e => { e.stopPropagation(); setSelectedFile(null); if (fileRef.current) fileRef.current.value = ''; }}
            >
              <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2.5}>
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        ) : (
          <>
            <div className="dropzone-upload-icon">
              <UploadCloudIcon color="#6366f1" />
            </div>
            <p className="dropzone-title">Drop your document here</p>
            <p className="dropzone-sub">or <span className="dropzone-link">click to browse</span></p>
            <p className="dropzone-hint">PDF, DOCX, PPTX, XLSX · Max 50 MB</p>
          </>
        )}
      </div>

      {progress !== null && (
        <div className="progress-wrap">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      )}

      <button
        id="document-upload-btn"
        className="submit-btn"
        onClick={handleUpload}
        disabled={!selectedFile || progress !== null}
        style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-2))' }}
      >
        {progress !== null ? (
          <><span className="spinner spinner-sm" /> Processing…</>
        ) : (
          <>
            <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload and Index Document
          </>
        )}
      </button>

      <div style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {SUPPORTED_TYPES.map(t => (
            <span
              key={t.ext}
              style={{
                padding: '3px 10px',
                borderRadius: '999px',
                border: `1px solid ${t.color}30`,
                background: `${t.color}10`,
                color: t.color,
                fontSize: 12,
                fontWeight: 500,
              }}
            >
              {t.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── GitHub Panel ──────────────────────────────────────────────────────────────

function GitHubPanel({ addToast, updateToast }: PanelProps) {
  const [owner, setOwner] = useState('');
  const [repo, setRepo]   = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner.trim() || !repo.trim()) return;
    setLoading(true);
    const tid = addToast('loading', `Ingesting ${owner}/${repo}…`);
    try {
      const body: Record<string, unknown> = { owner: owner.trim(), repo: repo.trim() };
      if (token.trim()) body.token = token.trim();

      const res = await fetch(`${API_BASE}/ingest/github`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      updateToast(tid, 'success', `"${owner}/${repo}" ingested — ${data.chunks_stored} chunks indexed`);
      setOwner(''); setRepo(''); setToken('');
    } catch (err) {
      updateToast(tid, 'error', `Failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="panel-header">
        <div className="panel-title">
          <div className="panel-title-icon" style={{ background: 'rgba(192,132,252,0.1)' }}>
            <GithubIcon color="var(--col-github)" />
          </div>
          GitHub Repository
        </div>
        <p className="panel-desc">
          Ingest any public GitHub repository. Code files are parsed structurally — Python functions,
          classes, and markdown headings each become individually searchable chunks.
        </p>
      </div>

      <form id="github-ingest-form" onSubmit={handleSubmit} className="ingest-form">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div className="form-group">
            <label className="form-label" htmlFor="github-owner">
              Owner / Organization <span className="form-required">*</span>
            </label>
            <input
              id="github-owner"
              type="text"
              className="form-input"
              placeholder="octocat"
              value={owner}
              onChange={e => setOwner(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="github-repo">
              Repository Name <span className="form-required">*</span>
            </label>
            <input
              id="github-repo"
              type="text"
              className="form-input"
              placeholder="Hello-World"
              value={repo}
              onChange={e => setRepo(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="github-token">
            Personal Access Token <span className="form-optional">(optional, for private repos)</span>
          </label>
          <input
            id="github-token"
            type="password"
            className="form-input"
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            value={token}
            onChange={e => setToken(e.target.value)}
            autoComplete="off"
          />
          <p className="form-hint">
            Required for private repositories. Generate at GitHub → Settings → Developer settings → Personal access tokens.
          </p>
        </div>

        <button
          id="github-submit-btn"
          type="submit"
          className="submit-btn"
          disabled={loading || !owner.trim() || !repo.trim()}
          style={{ background: 'linear-gradient(135deg, #7c3aed, #c084fc)' }}
        >
          {loading ? (
            <><span className="spinner spinner-sm" /> Ingesting repository…</>
          ) : (
            <>
              <GithubIcon color="white" />
              Ingest Repository
            </>
          )}
        </button>
      </form>
    </div>
  );
}
