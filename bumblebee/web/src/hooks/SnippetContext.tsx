import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { Song, SnippetRange, ChainSnippet } from '../types';

interface SnippetContextValue {
  selectedLines: { start: number | null; end: number | null };
  chain: ChainSnippet[];
  selectStart: (lineIdx: number) => void;
  selectEnd: (lineIdx: number) => void;
  clearSelection: () => void;
  addToChain: (song: Song, range: SnippetRange) => void;
  removeFromChain: (id: string) => void;
  reorderChain: (newOrder: ChainSnippet[]) => void;
  clearChain: () => void;
  getSelectedRange: (lyrics: { timestamp_ms: number }[]) => SnippetRange | null;
  exportChain: () => Promise<Blob>;
}

const SnippetContext = createContext<SnippetContextValue | null>(null);

export function SnippetProvider({ children }: { children: ReactNode }) {
  const [selectedLines, setSelectedLines] = useState<{ start: number | null; end: number | null }>({
    start: null,
    end: null,
  });
  const [chain, setChain] = useState<ChainSnippet[]>([]);

  const selectStart = useCallback((lineIdx: number) => {
    setSelectedLines({ start: lineIdx, end: null });
  }, []);

  const selectEnd = useCallback((lineIdx: number) => {
    setSelectedLines(prev => ({ ...prev, end: lineIdx }));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedLines({ start: null, end: null });
  }, []);

  const addToChain = useCallback((song: Song, range: SnippetRange) => {
    const id = `snippet-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    const label = `${song.title} (${range.start_line}-${range.end_line})`;
    setChain(prev => [...prev, { id, song, range, label }]);
  }, []);

  const removeFromChain = useCallback((id: string) => {
    setChain(prev => prev.filter(s => s.id !== id));
  }, []);

  const reorderChain = useCallback((newOrder: ChainSnippet[]) => {
    setChain(newOrder);
  }, []);

  const clearChain = useCallback(() => {
    setChain([]);
  }, []);

  const exportChain = useCallback(async (): Promise<Blob> => {
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 1000));
    const chainData = JSON.stringify(chain, null, 2);
    return new Blob([chainData], { type: 'application/json' });
  }, [chain]);

  const getSelectedRange = useCallback(
    (lyrics: { timestamp_ms: number }[]): SnippetRange | null => {
      if (selectedLines.start === null) return null;
      const startLine = selectedLines.start;
      const endLine = selectedLines.end ?? selectedLines.start;
      const startIdx = Math.min(startLine, endLine);
      const endIdx = Math.max(startLine, endLine);
      if (startIdx < 0 || endIdx >= lyrics.length) return null;
      return {
        start_line: startIdx,
        end_line: endIdx,
        start_ms: lyrics[startIdx].timestamp_ms,
        end_ms: lyrics[endIdx].timestamp_ms,
      };
    },
    [selectedLines]
  );

  return (
    <SnippetContext.Provider
      value={{
        selectedLines,
        chain,
        selectStart,
        selectEnd,
        clearSelection,
        addToChain,
        removeFromChain,
        reorderChain,
        clearChain,
        getSelectedRange,
        exportChain,
      }}
    >
      {children}
    </SnippetContext.Provider>
  );
}

export function useSharedSnippet(): SnippetContextValue {
  const ctx = useContext(SnippetContext);
  if (!ctx) {
    throw new Error('useSharedSnippet must be used within a SnippetProvider');
  }
  return ctx;
}
