'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const LINKS = [
  {
    href: '/',
    label: 'Search',
    icon: (
      <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <circle cx="11" cy="11" r="8" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
      </svg>
    ),
  },
  {
    href: '/upload',
    label: 'Upload',
    icon: (
      <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
  {
    href: '/sources',
    label: 'Sources',
    icon: (
      <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
      </svg>
    ),
  },
];

export default function Navbar() {
  const pathname = usePathname();
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => setOnline(r.ok))
      .catch(() => setOnline(false));
  }, []);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <nav className="navbar">
      <Link href="/" className="navbar-logo">
        <div className="logo-mark">Z</div>
        <span className="logo-text">Zeph<span>yr</span></span>
      </Link>

      <div className="navbar-links">
        {LINKS.map(link => (
          <Link
            key={link.href}
            href={link.href}
            className={`nav-link${isActive(link.href) ? ' active' : ''}`}
          >
            {link.icon}
            {link.label}
          </Link>
        ))}
      </div>

      <div className="navbar-right">
        <div className="api-status">
          <span
            className={`status-dot${online === false ? ' offline' : ''}`}
            title={online === null ? 'Checking…' : online ? 'API online' : 'API offline'}
          />
          <span>{online === null ? 'Connecting…' : online ? 'API Online' : 'API Offline'}</span>
        </div>
      </div>
    </nav>
  );
}
