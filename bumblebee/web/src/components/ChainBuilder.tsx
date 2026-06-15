import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Link2, ArrowLeft, Trash2, GripVertical, Download, Music,
  Wand2, Loader2, ChevronUp, ChevronDown, Clock
} from 'lucide-react';
import { useSharedSnippet } from '../hooks/SnippetContext';

export default function ChainBuilder() {
  const navigate = useNavigate();
  const snippet = useSharedSnippet();

  const [isExporting, setIsExporting] = useState(false);
  const [exportDone, setExportDone] = useState(false);
  const [crossfadeMs, setCrossfadeMs] = useState(150);

  const moveItem = (index: number, direction: -1 | 1) => {
    const newOrder = [...snippet.chain];
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= newOrder.length) return;
    [newOrder[index], newOrder[newIndex]] = [newOrder[newIndex], newOrder[index]];
    snippet.reorderChain(newOrder);
  };

  const handleExportChain = async () => {
    setIsExporting(true);
    try {
      const blob = await snippet.exportChain();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'bumblebee_chain.json';
      a.click();
      URL.revokeObjectURL(url);
      setExportDone(true);
      setTimeout(() => setExportDone(false), 3000);
    } catch {
      // error
    } finally {
      setIsExporting(false);
    }
  };

  const totalDuration = snippet.chain.reduce((sum, item) => {
    return sum + (item.range.end_ms - item.range.start_ms);
  }, 0);

  return (
    <div className="max-w-5xl mx-auto px-6 py-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-amber-500" />
          <h1 className="text-2xl font-extrabold text-slate-900">Chain Builder</h1>
        </div>
      </div>

      {snippet.chain.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-16 text-center">
          <Link2 className="w-16 h-16 text-slate-200 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-700 mb-2">
            Your chain is empty
          </h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
            Add snippets from the lyric viewer to build your Bumblebee message.
            Chain multiple song snippets together to create a complete message.
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2.5 bg-amber-500 text-white rounded-xl font-medium
                       hover:bg-amber-600 transition-colors"
          >
            Start Searching
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900">Timeline</h2>
                <span className="text-sm text-slate-500 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {(totalDuration / 1000).toFixed(1)}s total
                </span>
              </div>

              {/* Visual Timeline Bar */}
              <div className="w-full h-10 bg-slate-100 rounded-lg overflow-hidden flex mb-6">
                {snippet.chain.map((item, index) => {
                  const dur = item.range.end_ms - item.range.start_ms;
                  const pct = (dur / totalDuration) * 100;
                  const colors = [
                    'bg-amber-400', 'bg-amber-500', 'bg-yellow-400',
                    'bg-orange-400', 'bg-amber-300',
                  ];
                  return (
                    <div
                      key={item.id}
                      className={`${colors[index % colors.length]} flex items-center justify-center
                                  text-xs font-medium text-white relative group cursor-pointer`}
                      style={{ width: `${pct}%` }}
                    >
                      <span className="truncate px-2">{index + 1}</span>
                      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2
                                      bg-slate-900 text-white text-xs rounded-lg px-2 py-1
                                      opacity-0 group-hover:opacity-100 transition-opacity
                                      pointer-events-none whitespace-nowrap z-10">
                        {item.song.title} ({(dur / 1000).toFixed(1)}s)
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Chain Items */}
              <div className="space-y-2">
                {snippet.chain.map((item, index) => {
                  const dur = item.range.end_ms - item.range.start_ms;
                  return (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 bg-slate-50 rounded-lg p-3 border border-slate-100
                                 hover:border-amber-200 transition-colors"
                    >
                      <div className="flex flex-col">
                        <button
                          onClick={() => moveItem(index, -1)}
                          disabled={index === 0}
                          className="p-0.5 text-slate-400 hover:text-slate-600 disabled:opacity-30"
                        >
                          <ChevronUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => moveItem(index, 1)}
                          disabled={index === snippet.chain.length - 1}
                          className="p-0.5 text-slate-400 hover:text-slate-600 disabled:opacity-30"
                        >
                          <ChevronDown className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <GripVertical className="w-4 h-4 text-slate-300" />

                      <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center
                                      text-xs font-bold text-amber-700 shrink-0">
                        {index + 1}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {item.song.title}
                        </p>
                        <p className="text-xs text-slate-500">
                          {item.song.artist} · {formatTs(item.range.start_ms)} → {formatTs(item.range.end_ms)}
                          {' · '}({(dur / 1000).toFixed(1)}s)
                        </p>
                      </div>

                      <button
                        onClick={() => snippet.removeFromChain(item.id)}
                        className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50
                                   transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Settings & Export */}
          <div className="space-y-4">
            {/* Crossfade Settings */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Export Settings</h3>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">
                    Crossfade Duration
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={0}
                      max={1000}
                      step={50}
                      value={crossfadeMs}
                      onChange={(e) => setCrossfadeMs(parseInt(e.target.value))}
                      className="flex-1 h-1 bg-slate-200 rounded-full accent-amber-500"
                    />
                    <span className="text-xs font-mono text-slate-600 w-12 text-right">
                      {crossfadeMs}ms
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>Snippets</span>
                    <span className="font-medium text-slate-700">{snippet.chain.length}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Total duration</span>
                    <span className="font-medium text-slate-700">{(totalDuration / 1000).toFixed(1)}s</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Export Actions */}
            <div className="space-y-2">
              <button
                onClick={handleExportChain}
                disabled={isExporting || snippet.chain.length === 0}
                className="w-full flex items-center justify-center gap-2 py-3 bg-amber-500
                           text-white rounded-xl font-medium hover:bg-amber-600 transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isExporting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Export Chain
                  </>
                )}
              </button>

              {exportDone && (
                <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 rounded-lg p-3">
                  <Wand2 className="w-4 h-4" />
                  Chain exported!
                </div>
              )}

              <button
                onClick={() => {
                  if (confirm('Clear all snippets from chain?')) {
                    snippet.clearChain();
                  }
                }}
                className="w-full py-2.5 border border-slate-200 text-slate-600 rounded-xl
                           text-sm font-medium hover:bg-slate-50 transition-colors"
              >
                Clear Chain
              </button>
            </div>

            {/* Message preview */}
            <div className="bg-slate-900 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-amber-400 mb-3 flex items-center gap-2">
                <Music className="w-4 h-4" />
                Your Bumblebee Message
              </h3>
              <div className="space-y-1.5">
                {snippet.chain.map((item, i) => (
                  <div key={item.id} className="flex items-start gap-2">
                    <span className="text-xs text-slate-600 shrink-0 mt-0.5">{i + 1}.</span>
                    <p className="text-sm text-slate-300 italic">
                      "{getPreviewText(item.song.title)}"
                    </p>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-500 text-center">
                This is your message, spoken like Bumblebee
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatTs(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function getPreviewText(title: string): string {
  const previews: Record<string, string> = {
    'Just Dance': 'Gonna be okay',
    "Don't Stop Believin'": "Don't stop believin'",
    'We Are the Champions': 'We are the champions',
    'Poker Face': "Can't read my poker face",
  };
  return previews[title] || title;
}
