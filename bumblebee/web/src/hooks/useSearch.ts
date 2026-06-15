import { useState, useCallback, useRef } from 'react';
import type { Match } from '../types';
import { searchLyrics } from '../api';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [searchTime, setSearchTime] = useState(0);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback(async (q: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(async () => {
      if (!q.trim()) {
        setResults([]);
        setSearchTime(0);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      const start = performance.now();

      try {
        const matches = await searchLyrics(q, 20);
        setResults(matches);
        setSearchTime((performance.now() - start) / 1000);
      } catch (err) {
        console.error('Search error:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  const handleQueryChange = useCallback((q: string) => {
    setQuery(q);
    search(q);
  }, [search]);

  const clear = useCallback(() => {
    setQuery('');
    setResults([]);
    setSelectedMatch(null);
    setSearchTime(0);
    if (debounceRef.current) clearTimeout(debounceRef.current);
  }, []);

  return {
    query,
    setQuery: handleQueryChange,
    results,
    isLoading,
    search,
    selectedMatch,
    setSelectedMatch,
    searchTime,
    clear,
  };
}
