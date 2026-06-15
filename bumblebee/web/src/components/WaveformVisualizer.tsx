import { useRef, useEffect, useState } from 'react';
import type { SnippetRange } from '../types';

interface WaveformVisualizerProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  snippetRange?: SnippetRange | null;
  onSeek?: (timeMs: number) => void;
  color?: string;
}

export default function WaveformVisualizer({
  isPlaying: _isPlaying,
  currentTime,
  duration,
  snippetRange,
  onSeek,
  color = '#f59e0b',
}: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [waveformData, setWaveformData] = useState<number[]>([]);

  // Generate mock waveform data on mount
  useEffect(() => {
    const bars = 200;
    const data: number[] = [];
    for (let i = 0; i < bars; i++) {
      // Create a pattern that looks like a real waveform
      const envelope = Math.sin((i / bars) * Math.PI) * 0.5 + 0.5;
      const noise = Math.random() * 0.6 + 0.2;
      data.push(envelope * noise);
    }
    setWaveformData(data);
  }, []);

  // Draw waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || waveformData.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const barWidth = w / waveformData.length;
    const progress = duration > 0 ? currentTime / duration : 0;

    ctx.clearRect(0, 0, w, h);

    // Draw snippet range background
    if (snippetRange && duration > 0) {
      const startX = (snippetRange.start_ms / duration) * w;
      const endX = (snippetRange.end_ms / duration) * w;
      ctx.fillStyle = '#fef3c7';
      ctx.fillRect(startX, 0, endX - startX, h);
    }

    // Draw bars
    waveformData.forEach((amp, i) => {
      const x = i * barWidth;
      const barHeight = amp * h * 0.8;
      const y = (h - barHeight) / 2;
      const barProgress = i / waveformData.length;

      if (barProgress <= progress) {
        ctx.fillStyle = color;
      } else {
        ctx.fillStyle = '#e2e8f0';
      }

      const gap = 1;
      ctx.fillRect(x + gap / 2, y, barWidth - gap, barHeight);
    });

    // Draw playhead
    if (duration > 0) {
      const playheadX = progress * w;
      ctx.strokeStyle = '#92400e';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, h);
      ctx.stroke();
    }
  }, [waveformData, currentTime, duration, snippetRange, color]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onSeek || !duration) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    const pct = x / rect.width;
    onSeek(pct * duration);
  };

  return (
    <div className="w-full h-24 bg-white rounded-xl border border-slate-200 overflow-hidden cursor-pointer">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        onClick={handleClick}
      />
    </div>
  );
}
