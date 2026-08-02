import type { Env } from "./env";
import { serverError } from "./respond";
import type { HeroesData, ItemsData, VersionIndex } from "./types";

const ARCHIVE_INDEX = "archive/index.json";

export class NotFoundError extends Error {
  constructor(message = "Not found") {
    super(message);
    this.name = "NotFoundError";
  }
}

async function getObject<T>(bucket: R2Bucket, key: string): Promise<T> {
  const object = await bucket.get(key);
  if (!object) throw new NotFoundError(`Resource '${key}' not found`);
  return (await object.json()) as T;
}

export class Storage {
  constructor(private readonly bucket: R2Bucket) {}

  static fromEnv(env: Env): Storage {
    return new Storage(env.DATA);
  }

  async latestItems(): Promise<ItemsData> {
    return getObject<ItemsData>(this.bucket, "items_data.json");
  }

  async latestHeroes(): Promise<HeroesData> {
    return getObject<HeroesData>(this.bucket, "heroes_data.json");
  }

  async versionIndex(): Promise<VersionIndex> {
    return getObject<VersionIndex>(this.bucket, ARCHIVE_INDEX);
  }

  async archivedItems(buildId: string): Promise<ItemsData> {
    return getObject<ItemsData>(this.bucket, `archive/${buildId}/items_data.json`);
  }

  async archivedHeroes(buildId: string): Promise<HeroesData> {
    return getObject<HeroesData>(this.bucket, `archive/${buildId}/heroes_data.json`);
  }
}

export function handleError(err: unknown): Response {
  if (err instanceof NotFoundError) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 404,
      headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
    });
  }
  return serverError();
}
