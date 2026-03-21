import fs from "fs";
import path from "path";

/**
 * Content storage abstraction.
 *
 * Supports two modes:
 * 1. Local filesystem (development) — serves from storefront/content/
 * 2. S3/R2 (production) — set STORAGE_BUCKET and AWS credentials
 *
 * File naming convention:
 *   content/{slug}/ebook.pdf
 *   content/{slug}/audiobook.mp3
 *   content/{slug}/sample-{narratorId}.mp3
 */

const CONTENT_DIR = path.join(process.cwd(), "content");

/** Only allow safe slug characters — no path traversal. */
function sanitizeSlug(value: string): string | null {
  if (!value || !/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(value)) return null;
  return value;
}

export interface StorageFile {
  buffer: Buffer;
  contentType: string;
  filename: string;
}

const CONTENT_TYPES: Record<string, string> = {
  ebook: "application/pdf",
  audiobook: "audio/mpeg",
};

const EXTENSIONS: Record<string, string> = {
  ebook: "pdf",
  audiobook: "mp3",
};

export async function getContentFile(
  slug: string,
  format: string
): Promise<StorageFile | null> {
  const safeSlug = sanitizeSlug(slug);
  if (!safeSlug) return null;

  // Production: use S3/R2
  if (process.env.STORAGE_BUCKET) {
    return getFromCloudStorage(safeSlug, format);
  }

  // Development: use local filesystem
  return getFromLocalStorage(safeSlug, format);
}

function getFromLocalStorage(
  slug: string,
  format: string
): StorageFile | null {
  const ext = EXTENSIONS[format];
  if (!ext) return null;

  const filePath = path.join(CONTENT_DIR, slug, `${format}.${ext}`);
  if (!fs.existsSync(filePath)) return null;

  return {
    buffer: fs.readFileSync(filePath),
    contentType: CONTENT_TYPES[format] || "application/octet-stream",
    filename: `${slug}.${ext}`,
  };
}

async function getFromCloudStorage(
  slug: string,
  format: string
): Promise<StorageFile | null> {
  const ext = EXTENSIONS[format];
  if (!ext) return null;

  const bucket = process.env.STORAGE_BUCKET!;
  const region = process.env.STORAGE_REGION || "auto";
  const endpoint = process.env.STORAGE_ENDPOINT;

  // S3-compatible API (works with AWS S3, Cloudflare R2, MinIO)
  const key = `${slug}/${format}.${ext}`;
  const url = endpoint
    ? `${endpoint}/${bucket}/${key}`
    : `https://${bucket}.s3.${region}.amazonaws.com/${key}`;

  try {
    const response = await fetch(url, {
      headers: {
        // For R2/public buckets. For private S3, use AWS SDK with signed requests.
        ...(process.env.STORAGE_AUTH_TOKEN
          ? { Authorization: `Bearer ${process.env.STORAGE_AUTH_TOKEN}` }
          : {}),
      },
    });

    if (!response.ok) {
      console.error(`Storage fetch failed for ${key}: ${response.status}`);
      return null;
    }

    const arrayBuffer = await response.arrayBuffer();
    return {
      buffer: Buffer.from(arrayBuffer),
      contentType: CONTENT_TYPES[format] || "application/octet-stream",
      filename: `${slug}.${ext}`,
    };
  } catch (err) {
    console.error(`Storage error for ${key}:`, err);
    return null;
  }
}

/**
 * Get a sample audio file for previewing a narrator.
 */
export async function getSampleFile(
  slug: string,
  narratorId: string
): Promise<StorageFile | null> {
  const safeSlug = sanitizeSlug(slug);
  const safeNarrator = sanitizeSlug(narratorId);
  if (!safeSlug || !safeNarrator) return null;

  const key = `sample-${safeNarrator}.mp3`;

  if (process.env.STORAGE_BUCKET) {
    // Cloud path: fetch directly instead of going through getFromCloudStorage,
    // which only knows about ebook/audiobook formats via the EXTENSIONS map.
    return getCloudSample(safeSlug, key);
  }

  const filePath = path.join(CONTENT_DIR, safeSlug, key);
  if (!fs.existsSync(filePath)) return null;

  return {
    buffer: fs.readFileSync(filePath),
    contentType: "audio/mpeg",
    filename: `${safeSlug}-sample.mp3`,
  };
}

async function getCloudSample(
  slug: string,
  filename: string
): Promise<StorageFile | null> {
  const bucket = process.env.STORAGE_BUCKET!;
  const region = process.env.STORAGE_REGION || "auto";
  const endpoint = process.env.STORAGE_ENDPOINT;

  const objectKey = `${slug}/${filename}`;
  const url = endpoint
    ? `${endpoint}/${bucket}/${objectKey}`
    : `https://${bucket}.s3.${region}.amazonaws.com/${objectKey}`;

  try {
    const response = await fetch(url, {
      headers: {
        ...(process.env.STORAGE_AUTH_TOKEN
          ? { Authorization: `Bearer ${process.env.STORAGE_AUTH_TOKEN}` }
          : {}),
      },
    });

    if (!response.ok) {
      console.error(`Storage fetch failed for ${objectKey}: ${response.status}`);
      return null;
    }

    const arrayBuffer = await response.arrayBuffer();
    return {
      buffer: Buffer.from(arrayBuffer),
      contentType: "audio/mpeg",
      filename: `${slug}-sample.mp3`,
    };
  } catch (err) {
    console.error(`Storage error for ${objectKey}:`, err);
    return null;
  }
}
