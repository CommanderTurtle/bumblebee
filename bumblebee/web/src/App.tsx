import { useCallback } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import SearchBar from './components/SearchBar';
import ResultsList from './components/ResultsList';
import LyricViewer from './components/LyricViewer';
import ChainBuilder from './components/ChainBuilder';
import { useSearch } from './hooks/useSearch';
import { SnippetProvider } from './hooks/SnippetContext';
import { Music2, Zap, Globe, Sparkles } from 'lucide-react';

function SearchPage() {
  const search = useSearch();

  const handleClear = useCallback(() => {
    search.clear();
  }, [search]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Hero */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2">
          Speak Through Song
        </h1>
        <p className="text-slate-500">
          Search your music library by lyrics, find the exact line, and export audio snippets.
        </p>
      </div>

      {/* Search */}
      <div className="mb-8">
        <SearchBar
          query={search.query}
          onQueryChange={search.setQuery}
          isLoading={search.isLoading}
          onClear={handleClear}
        />
      </div>

      {/* Results */}
      <ResultsList
        results={search.results}
        isLoading={search.isLoading}
        searchTime={search.searchTime}
        query={search.query}
      />
    </div>
  );
}

function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <div className="text-center mb-10">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600
                        flex items-center justify-center mx-auto mb-4">
          <Music2 className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Bumblebee</h1>
        <p className="text-slate-500">Speak Through Song</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <FeatureCard
          icon={<Zap className="w-5 h-5 text-amber-500" />}
          title="Lyric Search"
          description="Find songs by typing any lyrics you remember. Full-text search across your entire library."
        />
        <FeatureCard
          icon={<Globe className="w-5 h-5 text-amber-500" />}
          title="Audio Export"
          description="Export MP3 snippets of any lyric line or range. Choose bitrate quality."
        />
        <FeatureCard
          icon={<Sparkles className="w-5 h-5 text-amber-500" />}
          title="Chain Builder"
          description="Combine multiple snippets into a message. Crossfade between clips."
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3">How It Works</h2>
        <ol className="space-y-3 text-sm text-slate-600">
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center
                             text-xs font-bold shrink-0">1</span>
            <span>Search for lyrics you remember — Bumblebee finds the exact song and timestamp.</span>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center
                             text-xs font-bold shrink-0">2</span>
            <span>Click a lyric line to select your snippet. Shift+click to select a range.</span>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center
                             text-xs font-bold shrink-0">3</span>
            <span>Export as MP3 or add to a chain to build your message.</span>
          </li>
          <li className="flex gap-3">
            <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center
                             text-xs font-bold shrink-0">4</span>
            <span>Combine snippets in the Chain Builder with crossfades, then export your full message.</span>
          </li>
        </ol>
      </div>

      <div className="mt-6 text-center text-xs text-slate-400">
        Bumblebee v1.0.0 · Built with React, Vite, Tailwind CSS & Wavesurfer.js
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 text-center">
      <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center mx-auto mb-3">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
    </div>
  );
}

function App() {
  return (
    <HashRouter>
      <SnippetProvider>
        <div className="min-h-screen bg-slate-50">
          <Navbar />
          <main className="pt-14">
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/song/:songId" element={<LyricViewer />} />
              <Route path="/chain" element={<ChainBuilder />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </main>
        </div>
      </SnippetProvider>
    </HashRouter>
  );
}

export default App;
