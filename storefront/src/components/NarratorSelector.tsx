"use client";

import type { Narrator } from "@/lib/storybooks";

interface NarratorSelectorProps {
  narrators: Narrator[];
  onSelect: (narrator: Narrator) => void;
  selected?: string;
}

export default function NarratorSelector({
  narrators,
  onSelect,
  selected,
}: NarratorSelectorProps) {
  return (
    <div className="space-y-3">
      <h3 className="font-display text-lg font-semibold text-gray-900">
        Choose Your Narrator
      </h3>
      <div className="grid gap-3" role="radiogroup" aria-label="Select a narrator">
        {narrators.map((narrator) => (
          <button
            key={narrator.id}
            onClick={() => onSelect(narrator)}
            role="radio"
            aria-checked={selected === narrator.id}
            aria-label={`${narrator.name}: ${narrator.description}`}
            className={`text-left p-4 rounded-xl border-2 transition-all duration-200 ${
              selected === narrator.id
                ? "border-primary-500 bg-primary-50 shadow-sm"
                : "border-gray-100 bg-white hover:border-primary-200"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-200 to-primary-400 flex items-center justify-center text-lg shrink-0">
                {narrator.id.includes("child") ? "🧒" : "🎙️"}
              </div>
              <div>
                <span className="font-medium text-gray-900 block">
                  {narrator.name}
                </span>
                <span className="text-sm text-gray-500">
                  {narrator.description}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
