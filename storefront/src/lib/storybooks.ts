export interface Narrator {
  id: string;
  name: string;
  description: string;
  personaFile: string;
  sampleUrl?: string;
  tags: string[];
}

export interface Storybook {
  slug: string;
  title: string;
  subtitle?: string;
  author: string;
  illustrator?: string;
  ageRange: string;
  pageCount: number;
  wordCount: number;
  description: string;
  longDescription: string;
  coverImage: string;
  priceInCents: number;
  audiobookPriceInCents: number;
  bundlePriceInCents: number;
  narrators: Narrator[];
  themes: string[];
  featured: boolean;
  previewPages: number;
  stripePriceIds: {
    ebook: string;
    audiobook: string;
    bundle: string;
  };
}

// Narrators sourced from the persona library
export const narrators: Narrator[] = [
  {
    id: "narrator-childrens",
    name: "Sunny",
    description:
      "Warm and playful, perfect for bedtime stories. Gentle pacing with expressive character voices.",
    personaFile: "personas/examples/narrator-childrens.json",
    tags: ["warm", "playful", "bedtime", "ages 3-6"],
  },
  {
    id: "narrator-literary-female",
    name: "Claire",
    description:
      "Elegant and measured, bringing depth to picture books with emotional range.",
    personaFile: "personas/examples/narrator-literary-female.json",
    tags: ["elegant", "expressive", "ages 5-8"],
  },
  {
    id: "character-child",
    name: "Pip",
    description:
      "Bright and curious child voice, full of wonder. Great for stories told from a kid's perspective.",
    personaFile: "personas/examples/character-child.json",
    tags: ["curious", "energetic", "child-voice", "ages 3-6"],
  },
];

// Storybook catalog — sourced from existing projects + placeholders for growth
export const storybooks: Storybook[] = [
  {
    slug: "luna-the-little-cloud",
    title: "Luna the Little Cloud",
    subtitle: "A story about finding where you belong",
    author: "Louis Rosche",
    ageRange: "3–6",
    pageCount: 32,
    wordCount: 580,
    description:
      "Luna is a small cloud who doesn't know what kind of cloud she wants to be. Through a journey across the sky, she discovers that the best thing to be is yourself.",
    longDescription: `Luna lives high above the world, surrounded by clouds of every shape and size. The thunderclouds are loud and important. The rain clouds are needed and praised. The wispy cirrus clouds are elegant and admired.

But Luna? Luna is just... small.

When Luna sets off to find where she belongs, she discovers something the other clouds have forgotten: the sky is big enough for everyone, and the smallest cloud can carry the biggest heart.

A gentle story about self-acceptance, belonging, and the courage to be exactly who you are.`,
    coverImage: "/covers/luna-the-little-cloud.svg",
    priceInCents: 499,
    audiobookPriceInCents: 699,
    bundlePriceInCents: 899,
    narrators: [narrators[0], narrators[2]],
    themes: ["self-acceptance", "belonging", "courage", "identity"],
    featured: true,
    previewPages: 4,
    stripePriceIds: {
      ebook: "price_luna_ebook",
      audiobook: "price_luna_audiobook",
      bundle: "price_luna_bundle",
    },
  },
  {
    slug: "the-brave-little-raindrop",
    title: "The Brave Little Raindrop",
    subtitle: "Every drop matters",
    author: "Louis Rosche",
    ageRange: "3–5",
    pageCount: 32,
    wordCount: 420,
    description:
      "A tiny raindrop is afraid of falling. But when the flowers below are thirsty, she finds the courage to let go.",
    longDescription: `High in a rumbling cloud, a tiny raindrop named Remi clings to the edge, watching the world far below.

"What if I fall and disappear?" she whispers.

But down in the meadow, a wilting flower is waiting. And sometimes being brave means letting go — because even the smallest raindrop can make a whole garden grow.

A tender story about courage, purpose, and the beauty of becoming part of something bigger than yourself.`,
    coverImage: "/covers/the-brave-little-raindrop.svg",
    priceInCents: 499,
    audiobookPriceInCents: 699,
    bundlePriceInCents: 899,
    narrators: [narrators[0], narrators[1]],
    themes: ["courage", "purpose", "nature", "growth"],
    featured: true,
    previewPages: 4,
    stripePriceIds: {
      ebook: "price_raindrop_ebook",
      audiobook: "price_raindrop_audiobook",
      bundle: "price_raindrop_bundle",
    },
  },
  {
    slug: "where-shadows-sleep",
    title: "Where Shadows Sleep",
    subtitle: "A bedtime adventure for the bravest dreamers",
    author: "Louis Rosche",
    ageRange: "4–7",
    pageCount: 32,
    wordCount: 560,
    description:
      "When the lights go out, Milo discovers that the shadows in his room aren't scary — they're sleeping creatures who need a lullaby.",
    longDescription: `Every night when the lights go out, Milo sees them: shadows stretching across his walls, dark shapes that shift and whisper.

But tonight, Milo doesn't hide. Tonight, he listens.

And what he hears changes everything — because the shadows aren't monsters. They're tired creatures looking for a place to rest. All they need is someone brave enough to sing them to sleep.

A luminous bedtime story that transforms nighttime fears into wonder and compassion.`,
    coverImage: "/covers/where-shadows-sleep.svg",
    priceInCents: 499,
    audiobookPriceInCents: 699,
    bundlePriceInCents: 899,
    narrators: [narrators[0], narrators[1], narrators[2]],
    themes: ["bedtime", "courage", "imagination", "compassion"],
    featured: false,
    previewPages: 4,
    stripePriceIds: {
      ebook: "price_shadows_ebook",
      audiobook: "price_shadows_audiobook",
      bundle: "price_shadows_bundle",
    },
  },
];

export function getStorybook(slug: string): Storybook | undefined {
  return storybooks.find((b) => b.slug === slug);
}

export function getFeaturedStorybooks(): Storybook[] {
  return storybooks.filter((b) => b.featured);
}

export function getStorybooksByTheme(theme: string): Storybook[] {
  return storybooks.filter((b) =>
    b.themes.some((t) => t.toLowerCase().includes(theme.toLowerCase()))
  );
}
