import type { Metadata } from 'next';
import './globals.css';
import Navbar from './components/Navbar';

export const metadata: Metadata = {
  title: 'Zephyr — Enterprise AI Search',
  description:
    'Search across PDFs, Word documents, PowerPoints, Excel spreadsheets, and GitHub repositories with AI-powered semantic retrieval.',
  keywords: ['enterprise search', 'AI search', 'RAG', 'semantic search', 'Zephyr'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="bg-gradient" />
        <Navbar />
        {children}
      </body>
    </html>
  );
}
