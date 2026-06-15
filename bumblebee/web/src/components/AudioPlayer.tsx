import { useMemo } from 'react';
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from 'lucide-react';

interface AudioRange {
  start: number;
  end: number;
}

interface AudioPlayerProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  onToggle: () => void;
  onSeek: (timeMs: number) => void;
  onVolumeChange: (v: number) => void;
  snippetRange?: AudioRange | null;
}

function formatTime(ms: number): string {
  if (!ms || isNaN(ms)) return '0:00';
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function AudioPlayer({
  isPlaying,
  currentTime,
  duration,
  volume,
  onToggle,
  onSeek,
  onVolumeChange,
  snippetRange,
}: AudioPlayerProps) {
  const progress = useMemo(() => {
    if (!duration) return 0;
    return Math.min(100, Math.max(0, (currentTime / duration) * 100));
  }, [currentTime, duration]);

  const displayTime = snippetRange
    ? Math.max(0, currentTime - snippetRange.start)
    : currentTime;

  const displayDuration = snippetRange
    ? snippetRange.end - snippetRange.start
    : duration;

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    const targetMs = pct * duration;
    onSeek(targetMs);
  };

  const isMuted = volume === 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      {/* Progress Bar */}
      <div
        className="relative w-full h-2 bg-slate-100 rounded-full cursor-pointer overflow-hidden"
        onClick={handleProgressClick}
      >
        {snippetRange && duration > 0 && (
          <div
            className="h-full bg-amber-100 absolute rounded-full"
            style={{
              left: `${(snippetRange.start / duration) * 100}%`,
              width: `${((snippetRange.end - snippetRange.start) / duration) * 100}%`,
            }}
          />
        )}
        <div
          className="h-full bg-amber-500 rounded-full transition-all duration-100"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Time */}
      <div className="flex justify-between mt-1.5 text-xs text-slate-500 font-mono">
        <span>{formatTime(displayTime)}</span>
        <span>{formatTime(displayDuration)}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-1">
          <button
            onClick={() => onSeek(Math.max(0, currentTime - 5000))}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            onClick={onToggle}
            className="p-3 rounded-xl bg-amber-500 text-white hover:bg-amber-600
                       transition-colors shadow-sm"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>

          <button
            onClick={() => onSeek(Math.min(duration, currentTime + 5000))}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        {/* Volume */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onVolumeChange(isMuted ? 1 : 0)}
            className="p-1.5 rounded-md text-slate-500 hover:bg-slate-100 transition-colors"
          >
            {isMuted ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </button>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={volume}
            onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
            className="w-20 h-1 bg-slate-200 rounded-full appearance-none cursor-pointer
                       accent-amber-500"
          />
        </div>
      </div>
    </div>
  );
}
