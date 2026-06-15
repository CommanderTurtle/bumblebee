import { Search, X, Loader2 } from 'lucide-react';

interface SearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  isLoading: boolean;
  onClear: () => void;
}

export default function SearchBar({ query, onQueryChange, isLoading, onClear }: SearchBarProps) {
  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-slate-400" />
          )}
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search lyrics... (e.g. 'gonna be okay')"
          className="w-full pl-12 pr-12 py-4 text-lg bg-white border border-slate-200 rounded-2xl
                     shadow-sm placeholder:text-slate-400
                     focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent
                     transition-all"
          autoFocus
        />

        {query && (
          <button
            onClick={onClear}
            className="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
