export interface LyricLine {
  timestamp_ms: number;
  text: string;
  timestamp_str: string;
}

export interface Song {
  id: string;
  file_path: string;
  title: string;
  artist: string;
  album: string;
  duration_ms: number;
  lrc_path: string | null;
}

export interface Match {
  song: Song;
  matched_line: LyricLine;
  context_before: LyricLine[];
  context_after: LyricLine[];
  match_score: number;
  match_type: string;
}

export interface SnippetRange {
  start_line: number;
  end_line: number;
  start_ms: number;
  end_ms: number;
}

export interface ChainSnippet {
  id: string;
  song: Song;
  range: SnippetRange;
  label: string;
}
