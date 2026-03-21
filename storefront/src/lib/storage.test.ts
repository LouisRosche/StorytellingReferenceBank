import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";
import path from "path";

const CONTENT_DIR = path.join(process.cwd(), "content");

describe("storage", () => {
  let existsSyncSpy: ReturnType<typeof vi.spyOn>;
  let readFileSyncSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.resetModules();
    delete process.env.STORAGE_BUCKET;
    delete process.env.STORAGE_REGION;
    delete process.env.STORAGE_ENDPOINT;
    delete process.env.STORAGE_AUTH_TOKEN;
    existsSyncSpy = vi.spyOn(fs, "existsSync");
    readFileSyncSpy = vi.spyOn(fs, "readFileSync");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getContentFile - local storage", () => {
    it("returns null for unknown format", async () => {
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "vinyl");
      expect(result).toBeNull();
    });

    it("returns null when file does not exist", async () => {
      existsSyncSpy.mockReturnValue(false);
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "ebook");
      expect(result).toBeNull();
    });

    it("returns ebook file with correct content type", async () => {
      existsSyncSpy.mockReturnValue(true);
      readFileSyncSpy.mockReturnValue(Buffer.from("pdf-data"));
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "ebook");
      expect(result).toEqual({
        buffer: Buffer.from("pdf-data"),
        contentType: "application/pdf",
        filename: "test-book.pdf",
      });
      expect(readFileSyncSpy).toHaveBeenCalledWith(
        path.join(CONTENT_DIR, "test-book", "ebook.pdf")
      );
    });

    it("returns audiobook file with correct content type", async () => {
      existsSyncSpy.mockReturnValue(true);
      readFileSyncSpy.mockReturnValue(Buffer.from("audio-data"));
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("my-book", "audiobook");
      expect(result).toEqual({
        buffer: Buffer.from("audio-data"),
        contentType: "audio/mpeg",
        filename: "my-book.mp3",
      });
    });
  });

  describe("getContentFile - cloud storage", () => {
    it("fetches from S3 URL when STORAGE_BUCKET is set", async () => {
      process.env.STORAGE_BUCKET = "my-bucket";
      process.env.STORAGE_REGION = "us-east-1";
      const mockResponse = {
        ok: true,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(4)),
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "ebook");
      expect(result).not.toBeNull();
      expect(result!.contentType).toBe("application/pdf");
      expect(fetch).toHaveBeenCalledWith(
        "https://my-bucket.s3.us-east-1.amazonaws.com/test-book/ebook.pdf",
        expect.any(Object)
      );
    });

    it("uses custom endpoint when STORAGE_ENDPOINT is set", async () => {
      process.env.STORAGE_BUCKET = "my-bucket";
      process.env.STORAGE_ENDPOINT = "https://r2.example.com";
      const mockResponse = {
        ok: true,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(4)),
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));
      const { getContentFile } = await import("./storage");
      await getContentFile("test-book", "ebook");
      expect(fetch).toHaveBeenCalledWith(
        "https://r2.example.com/my-bucket/test-book/ebook.pdf",
        expect.any(Object)
      );
    });

    it("returns null when cloud fetch fails", async () => {
      process.env.STORAGE_BUCKET = "my-bucket";
      const mockResponse = { ok: false, status: 404 };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "ebook");
      expect(result).toBeNull();
    });

    it("returns null on network error", async () => {
      process.env.STORAGE_BUCKET = "my-bucket";
      vi.stubGlobal(
        "fetch",
        vi.fn().mockRejectedValue(new Error("Network error"))
      );
      const { getContentFile } = await import("./storage");
      const result = await getContentFile("test-book", "ebook");
      expect(result).toBeNull();
    });

    it("includes auth token when STORAGE_AUTH_TOKEN is set", async () => {
      process.env.STORAGE_BUCKET = "my-bucket";
      process.env.STORAGE_AUTH_TOKEN = "secret-token";
      const mockResponse = {
        ok: true,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(4)),
      };
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockResponse));
      const { getContentFile } = await import("./storage");
      await getContentFile("test-book", "ebook");
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: { Authorization: "Bearer secret-token" },
        })
      );
    });
  });

  describe("getSampleFile", () => {
    it("returns sample audio from local storage", async () => {
      existsSyncSpy.mockReturnValue(true);
      readFileSyncSpy.mockReturnValue(Buffer.from("sample-data"));
      const { getSampleFile } = await import("./storage");
      const result = await getSampleFile("test-book", "narrator-warm");
      expect(result).toEqual({
        buffer: Buffer.from("sample-data"),
        contentType: "audio/mpeg",
        filename: "test-book-sample.mp3",
      });
    });

    it("returns null when sample does not exist", async () => {
      existsSyncSpy.mockReturnValue(false);
      const { getSampleFile } = await import("./storage");
      const result = await getSampleFile("test-book", "narrator-warm");
      expect(result).toBeNull();
    });
  });
});
