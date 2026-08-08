import type { Env } from "./env";
import { serverError } from "./respond";
import type { HeroesData, ItemsData, VersionEntry, VersionIndex } from "./types";

const ARCHIVE_INDEX = "archive/index.json";
const ARCHIVE_PREFIX = "archive/";

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

async function tryGetObject<T>(bucket: R2Bucket, key: string): Promise<T | undefined> {
  try {
    return await getObject<T>(bucket, key);
  } catch (err) {
    if (err instanceof NotFoundError) return undefined;
    throw err;
  }
}

async function listBuildIds(bucket: R2Bucket): Promise<string[]> {
  const ids: string[] = [];
  let cursor: string | undefined;
  do {
    const page = await bucket.list({
      prefix: ARCHIVE_PREFIX,
      delimiter: "/",
      ...(cursor ? { cursor } : {}),
    });
    for (const prefix of page.delimitedPrefixes ?? []) {
      const id = prefix.slice(ARCHIVE_PREFIX.length).replace(/\/+$/, "");
      if (id && id !== "index.json") ids.push(id);
    }
    cursor = page.truncated ? page.cursor : undefined;
  } while (cursor);
  return ids;
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
    const [folderIds, stored] = await Promise.all([
      listBuildIds(this.bucket),
      tryGetObject<VersionIndex>(this.bucket, ARCHIVE_INDEX).then((idx) => idx?.builds ?? {}),
    ]);
    const builds: Record<string, VersionEntry> = {};
    for (const id of folderIds) {
      if (stored[id]) {
        builds[id] = stored[id];
      } else {
        builds[id] = await this.entryFromArchive(id);
      }
    }
    return { builds };
  }

  private async entryFromArchive(buildId: string): Promise<VersionEntry> {
    const [items, heroes] = await Promise.all([
      tryGetObject<ItemsData>(this.bucket, `archive/${buildId}/items_data.json`),
      tryGetObject<HeroesData>(this.bucket, `archive/${buildId}/heroes_data.json`),
    ]);
    const meta = items?._metadata ?? heroes?._metadata;
    return {
      build_id: buildId,
      captured_at: meta?.captured_at ?? "",
      manifests: meta?.manifests ?? {},
      items_count: items?._metadata?.count,
      items_hash: undefined,
      heroes_count: heroes?._metadata?.count,
      heroes_hash: undefined,
    };
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
