import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Star, Play, Pause, Music, Disc, Clock,
  MousePointerClick, Keyboard, AlertCircle
} from 'lucide-react';
import type { LyricLine, Song } from '../types';
import { getSongLyrics, getSong } from '../api';
import { useAudio } from '../hooks/useAudio';
import { useSharedSnippet } from '../hooks/SnippetContext';
import AudioPlayer from './AudioPlayer';
import WaveformVisualizer from './WaveformVisualizer';
import ExportPanel from './ExportPanel';

export default function LyricViewer() {
  const { songId } = useParams<{ songId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const matchState = location.state as { matchedLine?: LyricLine; matchScore?: number } | null;

  const [song, setSong] = useState<Song | null>(null);
  const [lyrics, setLyrics] = useState<LyricLine[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentLyricIndex, setCurrentLyricIndex] = useState(-1);

  const audio = useAudio();
  const snippet = useSharedSnippet();

  const lyricsContainerRef = useRef<HTMLDivElement>(null);
  const lyricRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Load song data
  useEffect(() => {
    if (!songId) return;

    setIsLoading(true);
    Promise.all([getSong(songId), getSongLyrics(songId)])
      .then(([songData, lyricsData]) => {
        setSong(songData);
        setLyrics(lyricsData);

        // Find matched line index
        if (matchState?.matchedLine) {
          const idx = lyricsData.findIndex(
            l => l.timestamp_ms === matchState.matchedLine!.timestamp_ms
          );
          if (idx >= 0) {
            setCurrentLyricIndex(idx);
            setTimeout(() => {
              lyricRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
          }
        }
      })
      .finally(() => setIsLoading(false));
  }, [songId, matchState?.matchedLine?.timestamp_ms]);

  // Sync current lyric with audio playback
  useEffect(() => {
    if (!audio.isPlaying || lyrics.length === 0) return;

    const idx = lyrics.findIndex((line, i) => {
      const nextLine = lyrics[i + 1];
      return (
        audio.currentTime >= line.timestamp_ms &&
        (!nextLine || audio.currentTime < nextLine.timestamp_ms)
      );
    });

    if (idx >= 0 && idx !== currentLyricIndex) {
      setCurrentLyricIndex(idx);
      lyricRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [audio.currentTime, audio.isPlaying, lyrics, currentLyricIndex]);

  const handleLyricClick = useCallback((index: number, event: React.MouseEvent) => {
    if (event.shiftKey) {
      snippet.selectEnd(index);
    } else {
      snippet.selectStart(index);
    }
  }, [snippet]);

  const handlePlayLine = useCallback((line: LyricLine) => {
    if (!song) return;
    const endMs = Math.min(line.timestamp_ms + 5000, song.duration_ms);
    audio.play(`/api/audio/${song.id}`, { start: line.timestamp_ms, end: endMs }, 'line');
  }, [song, audio]);

  const snippetRange = snippet.getSelectedRange(lyrics);

  const handlePlaySnippet = useCallback(() => {
    if (!song || !snippetRange) return;
    audio.play(`/api/audio/${song.id}`, {
      start: snippetRange.start_ms,
      end: snippetRange.end_ms + 2000,
    }, 'snippet');
  }, [song, snippetRange, audio]);

  const handlePlayFull = useCallback(() => {
    if (!song) return;
    audio.play(`/api/audio/${song.id}`, undefined, 'full');
  }, [song, audio]);

  const isLineMatched = (line: LyricLine) =>
    matchState?.matchedLine?.timestamp_ms === line.timestamp_ms;

  const isLineSelected = (index: number) => {
    if (snippet.selectedLines.start === null) return false;
    if (snippet.selectedLines.end === null) return index === snippet.selectedLines.start;
    const start = Math.min(snippet.selectedLines.start, snippet.selectedLines.end);
    const end = Math.max(snippet.selectedLines.start, snippet.selectedLines.end);
    return index >= start && index <= end;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!song || lyrics.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-center">
        <Music className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-slate-700 mb-2">Song not found</h2>
        <button
          onClick={() => navigate('/')}
          className="text-amber-600 hover:text-amber-700 font-medium"
        >
          Back to search
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-6">
      {/* Error Toast */}
      {audio.error.show && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg px-4">
          <div className="bg-slate-900 text-white rounded-xl shadow-lg px-4 py-3 flex items-start gap-3"
               style={{ animation: 'fadeInDown 0.3s ease-out' }}>
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1 text-sm min-w-0">
              <p className="font-medium text-amber-400 mb-0.5">Backend Required</p>
              <p className="text-slate-300 break-words">{audio.error.message}</p>
            </div>
            <button
              onClick={audio.clearError}
              className="text-slate-400 hover:text-white shrink-0"
            >
              <span className="sr-only">Dismiss</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
      )}

      {/* Back button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700
                   mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to search
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Song Header */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600
                              flex items-center justify-center shrink-0">
                <Disc className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-extrabold text-slate-900 truncate">
                  {song.title}
                </h1>
                <p className="text-base text-slate-600 mt-0.5">{song.artist}</p>
                <p className="text-sm text-slate-400 mt-0.5">{song.album}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock className="w-3 h-3" />
                    {formatDuration(song.duration_ms)}
                  </span>
                  {matchState?.matchScore && (
                    <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50
                                     px-2 py-0.5 rounded-full">
                      <Star className="w-3 h-3" />
                      {Math.round(matchState.matchScore * 100)}% match
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={handlePlayFull}
                className="shrink-0 flex items-center gap-2 px-4 py-2.5 bg-amber-500 text-white
                           rounded-xl font-medium hover:bg-amber-600 transition-colors shadow-sm"
              >
                {audio.isPlaying && audio.playMode === 'full' ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {audio.isPlaying && audio.playMode === 'full' ? 'Pause' : 'Play'}
              </button>
            </div>
          </div>

          {/* Waveform */}
          <WaveformVisualizer
            isPlaying={audio.isPlaying}
            currentTime={audio.currentTime}
            duration={audio.duration || song.duration_ms}
            snippetRange={snippetRange}
            onSeek={audio.seek}
          />

          {/* Audio Player Controls */}
          <AudioPlayer
            isPlaying={audio.isPlaying}
            currentTime={audio.currentTime}
            duration={audio.duration || song.duration_ms}
            volume={audio.volume}
            onToggle={audio.toggle}
            onSeek={audio.seek}
            onVolumeChange={audio.setVolume}
            snippetRange={audio.activeRange}
          />

          {/* Selection Hint */}
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <MousePointerClick className="w-3 h-3" />
              Click line = set start
            </span>
            <span className="flex items-center gap-1">
              <Keyboard className="w-3 h-3" />
              Shift+click = set range
            </span>
          </div>

          {/* Lyrics List */}
          <div
            ref={lyricsContainerRef}
            className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
          >
            <div className="divide-y divide-slate-50 max-h-[600px] overflow-y-auto">
              {lyrics.map((line, index) => {
                const matched = isLineMatched(line);
                const selected = isLineSelected(index);
                const current = currentLyricIndex === index && audio.isPlaying;

                return (
                  <div
                    key={index}
                    ref={(el) => { lyricRefs.current[index] = el; }}
                    onClick={(e) => handleLyricClick(index, e)}
                    className={`group flex items-center gap-3 px-4 py-2 transition-all cursor-pointer
                      ${matched ? 'lyric-line matched' : ''}
                      ${selected ? 'lyric-line selected' : ''}
                      ${current ? 'lyric-line current' : 'lyric-line'}
                      ${!matched && !selected && !current ? 'lyric-line' : ''}
                    `}
                  >
                    <span className="text-xs text-slate-400 font-mono w-12 text-right shrink-0">
                      {line.timestamp_str}
                    </span>
                    <span className={`flex-1 text-sm ${
                      matched ? 'font-medium' :
                      selected ? 'font-medium' :
                      current ? 'font-medium' : ''
                    }`}>
                      {line.text}
                    </span>
                    {matched && (
                      <Star className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePlayLine(line);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-400
                                 hover:text-amber-600 hover:bg-amber-50 transition-all"
                      title="Preview this line"
                    >
                      <Play className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <ExportPanel
            song={song}
            range={snippetRange}
            onAddToChain={snippet.addToChain}
          />

          {/* Play Snippet Button */}
          {snippetRange && (
            <button
              onClick={handlePlaySnippet}
              className="w-full flex items-center justify-center gap-2 py-3 bg-slate-900
                         text-white rounded-xl font-medium hover:bg-slate-800 transition-colors"
            >
              {audio.isPlaying && (audio.playMode === 'snippet' || audio.playMode === 'line') ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {audio.isPlaying && (audio.playMode === 'snippet' || audio.playMode === 'line')
                ? 'Pause Snippet'
                : 'Play Snippet'}
            </button>
          )}

          {/* Chain Preview */}
          {snippet.chain.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">
                Chain ({snippet.chain.length} snippets)
              </h3>
              <div className="space-y-2">
                {snippet.chain.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-2 text-sm bg-slate-50 rounded-lg px-3 py-2"
                  >
                    <Music className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                    <span className="text-slate-700 truncate flex-1">{item.label}</span>
                  </div>
                ))}
              </div>
              <button
                onClick={() => navigate('/chain')}
                className="w-full mt-3 text-center text-sm text-amber-600 hover:text-amber-700
                           font-medium py-2 border border-amber-200 rounded-lg hover:bg-amber-50
                           transition-colors"
              >
                Open Chain Builder →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Hidden audio element */}
      <audio ref={audio.audioRef} />
    </div>
  );
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
