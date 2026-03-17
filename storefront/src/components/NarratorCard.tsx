import type { Narrator } from "@/lib/storybooks";

export default function NarratorCard({ narrator }: { narrator: Narrator }) {
  return (
    <div className="card p-6">
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-200 to-primary-400 flex items-center justify-center text-2xl mb-4">
        {narrator.id.includes("child") ? "🧒" : "🎙️"}
      </div>
      <h3 className="font-display text-lg font-bold text-gray-900">
        {narrator.name}
      </h3>
      <p className="text-sm text-gray-600 mt-2">{narrator.description}</p>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {narrator.tags.map((tag) => (
          <span
            key={tag}
            className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full"
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
