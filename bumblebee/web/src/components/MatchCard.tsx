import { useNavigate } from 'react-router-dom';
import { Play, Star, Clock, Music } from 'lucide-react';
import type { Match } from '../types';

interface MatchCardProps {
  match: Match;
  index: number;
  onPlay?: (match: Match) => void;
}

export default function MatchCard({ match, index, onPlay }: MatchCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/song/${match.song.id}`, {
      state: { matchedLine: match.matched_line, matchScore: match.match_score },
    });
  };

  const scorePercent = Math.round(match.match_score * 100);
  const scoreColor =
    scorePercent >= 90 ? 'bg-green-100 text-green-800' :
    scorePercent >= 70 ? 'bg-amber-100 text-amber-800' :
    'bg-slate-100 text-slate-600';

  return (
    <div
      className="group bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md
                 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer overflow-hidden"
      onClick={handleClick}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
              <Music className="w-4 h-4 text-slate-500" />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-slate-900 truncate">
                {match.song.title}
              </h3>
              <p className="text-sm text-slate-500">
                {match.song.artist} · {match.song.album}
              </p>
            </div>
          </div>
          <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-semibold ${scoreColor}`}>
            {scorePercent}%
          </span>
        </div>
      </div>

      {/* Matched Line */}
      <div className="px-5 py-2.5 bg-amber-50 border-y border-amber-100">
        <div className="flex items-center gap-2">
          <Star className="w-3.5 h-3.5 text-amber-500 shrink-0" />
          <span className="text-amber-900 font-medium text-sm">{match.matched_line.text}</span>
          <span className="ml-auto text-xs text-amber-600 font-mono shrink-0 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {match.matched_line.timestamp_str}
          </span>
        </div>
      </div>

      {/* Context */}
      <div className="px-5 py-3">
        {match.context_before.map((line, i) => (
          <p key={`before-${i}`} className="text-sm text-slate-400 truncate pl-5">
            {line.text}
          </p>
        ))}
        <p className="text-sm text-amber-900 font-medium truncate pl-5">
          {match.matched_line.text}
        </p>
        {match.context_after.map((line, i) => (
          <p key={`after-${i}`} className="text-sm text-slate-400 truncate pl-5">
            {line.text}
          </p>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-2.5 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-400">
          {match.match_type} match
        </span>
        {onPlay && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPlay(match);
            }}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-500
                       hover:text-amber-600 transition-colors px-2 py-1 rounded-md hover:bg-amber-50"
          >
            <Play className="w-3.5 h-3.5" />
            Preview
          </button>
        )}
      </div>
    </div>
  );
}
