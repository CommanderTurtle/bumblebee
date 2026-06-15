import { useState } from 'react';
import { Download, X, FileAudio, Check, Loader2 } from 'lucide-react';
import type { Song, SnippetRange } from '../types';
import { exportSnippet } from '../api';

interface SnippetExporterProps {
  song: Song;
  range: SnippetRange;
  onClose: () => void;
}

type ExportState = 'idle' | 'exporting' | 'done' | 'error';

export default function SnippetExporter({ song, range, onClose }: SnippetExporterProps) {
  const [filename, setFilename] = useState(`bumblebee_snippet_${song.title.toLowerCase().replace(/\s+/g, '_')}`);
  const [bitrate, setBitrate] = useState('192');
  const [state, setState] = useState<ExportState>('idle');
  const [blob, setBlob] = useState<Blob | null>(null);

  const durationSec = ((range.end_ms - range.start_ms) / 1000).toFixed(2);

  const handleExport = async () => {
    setState('exporting');
    try {
      const result = await exportSnippet(
        song.id,
        range.start_ms,
        range.end_ms,
        filename,
        `${bitrate}k`
      );
      setBlob(result);
      setState('done');
    } catch {
      setState('error');
    }
  };

  const handleDownload = () => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.mp3`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileAudio className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-slate-900">Export Snippet</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Song info */}
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-sm font-medium text-slate-900">{song.title}</p>
            <p className="text-xs text-slate-500">{song.artist} · {song.album}</p>
            <p className="text-xs text-slate-400 mt-1">
              Snippet: {durationSec}s · {formatTs(range.start_ms)} → {formatTs(range.end_ms)}
            </p>
          </div>

          {/* Filename */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Filename
            </label>
            <div className="flex">
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                disabled={state === 'exporting' || state === 'done'}
                className="flex-1 px-3 py-2 border border-slate-200 rounded-l-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent
                           disabled:bg-slate-50 disabled:text-slate-500"
              />
              <span className="px-3 py-2 bg-slate-100 border border-l-0 border-slate-200 rounded-r-lg
                               text-sm text-slate-500 font-mono">
                .mp3
              </span>
            </div>
          </div>

          {/* Bitrate */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Bitrate Quality
            </label>
            <div className="flex gap-2">
              {['128', '192', '320'].map((b) => (
                <button
                  key={b}
                  onClick={() => setBitrate(b)}
                  disabled={state === 'exporting' || state === 'done'}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border transition-colors ${
                    bitrate === b
                      ? 'bg-amber-50 border-amber-300 text-amber-700'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  } disabled:opacity-50`}
                >
                  {b}k
                </button>
              ))}
            </div>
          </div>

          {/* Status */}
          {state === 'done' && (
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 rounded-lg p-3">
              <Check className="w-4 h-4" />
              Export complete! Ready to download.
            </div>
          )}
          {state === 'error' && (
            <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
              Export failed. Please try again.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex gap-3">
          {state === 'done' ? (
            <>
              <button
                onClick={handleDownload}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-500
                           text-white rounded-lg font-medium hover:bg-green-600 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download MP3
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium
                           text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Close
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleExport}
                disabled={state === 'exporting' || !filename.trim()}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-amber-500
                           text-white rounded-lg font-medium hover:bg-amber-600 transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {state === 'exporting' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Export MP3
                  </>
                )}
              </button>
              <button
                onClick={onClose}
                disabled={state === 'exporting'}
                className="px-4 py-2.5 border border-slate-200 rounded-lg text-sm font-medium
                           text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function formatTs(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
