import { Search, Clock } from 'lucide-react';
import type { Match } from '../types';
import MatchCard from './MatchCard';

interface ResultsListProps {
  results: Match[];
  isLoading: boolean;
  searchTime: number;
  query: string;
  onPlayMatch?: (match: Match) => void;
}

export default function ResultsList({ results, isLoading, searchTime, query, onPlayMatch }: ResultsListProps) {
  if (!query.trim() && results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
          <Search className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-700 mb-1">
          Search for lyrics to find songs
        </h3>
        <p className="text-sm text-slate-500 max-w-md">
          Type lyrics you remember and Bumblebee will find the matching song, artist, and exact timestamp.
        </p>
        <div className="mt-6 flex flex-wrap gap-2 justify-center">
          {['gonna be okay', "don't stop believin'", 'we are the champions', 'poker face'].map((suggestion) => (
            <span
              key={suggestion}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-sm text-slate-600
                         hover:border-amber-300 hover:text-amber-700 cursor-pointer transition-colors"
            >
              {suggestion}
            </span>
          ))}
        </div>
      </div>
    );
  }

  if (isLoading && results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm text-slate-500">Searching lyrics...</p>
      </div>
    );
  }

  if (results.length === 0 && query.trim()) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
          <Search className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-700 mb-1">No matches found</h3>
        <p className="text-sm text-slate-500">
          Try different lyrics or a shorter phrase.
        </p>
      </div>
    );
  }

  const songCount = new Set(results.map(r => r.song.id)).size;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700">
            {results.length} match{results.length !== 1 ? 'es' : ''}
          </span>
          <span className="text-xs text-slate-400">
            in {songCount} song{songCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Clock className="w-3 h-3" />
          {searchTime.toFixed(2)}s
        </div>
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 gap-4">
        {results.map((match, index) => (
          <MatchCard
            key={`${match.song.id}-${match.matched_line.timestamp_ms}-${index}`}
            match={match}
            index={index}
            onPlay={onPlayMatch}
          />
        ))}
      </div>
    </div>
  );
}
