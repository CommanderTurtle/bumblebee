import { useState } from 'react';
import { Download, FileAudio, Wand2 } from 'lucide-react';
import type { Song, SnippetRange } from '../types';
import SnippetExporter from './SnippetExporter';

interface ExportPanelProps {
  song: Song;
  range: SnippetRange | null;
  onAddToChain: (song: Song, range: SnippetRange) => void;
}

export default function ExportPanel({ song, range, onAddToChain }: ExportPanelProps) {
  const [showExporter, setShowExporter] = useState(false);

  if (!range) {
    return (
      <div className="bg-slate-50 rounded-xl border border-dashed border-slate-300 p-6 text-center">
        <FileAudio className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-sm text-slate-500">
          Click a lyric line to select a snippet for export
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Shift+click another line to select a range
        </p>
      </div>
    );
  }

  const durationSec = ((range.end_ms - range.start_ms) / 1000).toFixed(2);

  return (
    <>
      <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-amber-600" />
          <h3 className="text-sm font-semibold text-amber-900">Selected Snippet</h3>
        </div>

        <div className="text-sm text-amber-800 space-y-1">
          <p>
            <span className="font-mono text-xs text-amber-600">{formatTs(range.start_ms)}</span>
            {' → '}
            <span className="font-mono text-xs text-amber-600">{formatTs(range.end_ms)}</span>
            {' '}
            <span className="text-xs text-amber-500">({durationSec}s)</span>
          </p>
          <p className="text-xs text-amber-600">
            Lines {range.start_line + 1} to {range.end_line + 1}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowExporter(true)}
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-amber-500
                       text-white rounded-lg text-sm font-medium hover:bg-amber-600 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export MP3
          </button>
          <button
            onClick={() => onAddToChain(song, range)}
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-white
                       border border-amber-300 text-amber-700 rounded-lg text-sm font-medium
                       hover:bg-amber-100 transition-colors"
          >
            + Add to Chain
          </button>
        </div>
      </div>

      {showExporter && (
        <SnippetExporter
          song={song}
          range={range}
          onClose={() => setShowExporter(false)}
        />
      )}
    </>
  );
}

function formatTs(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
