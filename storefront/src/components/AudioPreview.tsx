"use client";

import { useRef, useState } from "react";
import type { Narrator } from "@/lib/storybooks";

interface AudioPreviewProps {
  narrator: Narrator;
}

export default function AudioPreview({ narrator }: AudioPreviewProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  if (!narrator.sampleUrl) return null;

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play().catch(() => setError(true));
      setPlaying(true);
    }
  }

  function handleEnded() {
    setPlaying(false);
  }

  function handleError() {
    setError(true);
    setPlaying(false);
  }

  if (error) {
    return (
      <p className="text-xs text-gray-400 italic">
        Audio preview not yet available for {narrator.name}
      </p>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={togglePlay}
        aria-label={`${playing ? "Pause" : "Play"} sample from ${narrator.name}`}
        className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center hover:bg-primary-200 transition-colors text-sm"
      >
        {playing ? "⏸" : "▶"}
      </button>
      <span className="text-xs text-gray-500">
        {playing ? "Playing..." : `Preview ${narrator.name}'s voice`}
      </span>
      <audio
        ref={audioRef}
        src={narrator.sampleUrl}
        preload="none"
        onEnded={handleEnded}
        onError={handleError}
      />
    </div>
  );
}
