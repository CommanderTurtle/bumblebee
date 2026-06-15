import { useState, useRef, useCallback, useEffect } from 'react';

interface AudioRange {
  start: number;
  end: number;
}

interface AudioError {
  message: string;
  show: boolean;
}

export function useAudio() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [activeRange, setActiveRange] = useState<AudioRange | null>(null);
  const [playMode, setPlayMode] = useState<'full' | 'snippet' | 'line' | null>(null);
  const [error, setError] = useState<AudioError>({ message: '', show: false });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number | null>(null);

  const clearError = useCallback(() => {
    setError({ message: '', show: false });
  }, []);

  const showError = useCallback((message: string) => {
    setError({ message, show: true });
    setTimeout(() => setError({ message: '', show: false }), 5000);
  }, []);

  const updateTime = useCallback(() => {
    if (audioRef.current) {
      const t = audioRef.current.currentTime * 1000;
      setCurrentTime(t);

      if (activeRange && t >= activeRange.end) {
        audioRef.current.pause();
        audioRef.current.currentTime = activeRange.start / 1000;
        setIsPlaying(false);
        setPlayMode(null);
      }
    }
    rafRef.current = requestAnimationFrame(updateTime);
  }, [activeRange]);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
    };
  }, []);

  const play = useCallback((url: string, range?: AudioRange, mode?: 'full' | 'snippet' | 'line') => {
    if (!audioRef.current) return;

    clearError();

    if (range) {
      setActiveRange(range);
    } else {
      setActiveRange(null);
    }

    setPlayMode(mode || (range ? 'snippet' : 'full'));

    const audio = audioRef.current;

    if (audio.src !== url) {
      audio.src = url;
      audio.load();
    }

    if (range) {
      audio.currentTime = range.start / 1000;
    }

    const onLoaded = () => {
      setDuration(audio.duration * 1000);
    };

    const onEnded = () => {
      setIsPlaying(false);
      setPlayMode(null);
      if (range) {
        setCurrentTime(range.start);
      } else {
        setCurrentTime(0);
      }
    };

    const onError = () => {
      setIsPlaying(false);
      setPlayMode(null);
      showError(
        'Audio playback requires the Bumblebee backend. Run: uv run -m uvicorn bumblebee.web_api:app --port 8000'
      );
    };

    audio.addEventListener('loadedmetadata', onLoaded, { once: true });
    audio.addEventListener('ended', onEnded, { once: true });
    audio.addEventListener('error', onError, { once: true });

    audio.play().then(() => {
      setIsPlaying(true);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(updateTime);
    }).catch(() => {
      setIsPlaying(false);
      setPlayMode(null);
      showError(
        'Audio playback requires the Bumblebee backend. Run: uv run -m uvicorn bumblebee.web_api:app --port 8000'
      );
    });
  }, [updateTime, clearError, showError]);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
  }, []);

  const toggle = useCallback(() => {
    if (isPlaying) {
      pause();
    } else if (audioRef.current) {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        rafRef.current = requestAnimationFrame(updateTime);
      }).catch(() => {
        showError(
          'Audio playback requires the Bumblebee backend. Run: uv run -m uvicorn bumblebee.web_api:app --port 8000'
        );
      });
    }
  }, [isPlaying, pause, updateTime, showError]);

  const seek = useCallback((timeMs: number) => {
    if (audioRef.current) {
      const clampedTime = Math.max(0, Math.min(timeMs, duration));
      audioRef.current.currentTime = clampedTime / 1000;
      setCurrentTime(clampedTime);
    }
  }, [duration]);

  const setVolumeLevel = useCallback((v: number) => {
    if (audioRef.current) {
      audioRef.current.volume = v;
      setVolume(v);
    }
  }, []);

  return {
    isPlaying,
    currentTime,
    duration,
    volume,
    activeRange,
    playMode,
    error,
    clearError,
    play,
    pause,
    toggle,
    seek,
    setVolume: setVolumeLevel,
    audioRef,
  };
}
