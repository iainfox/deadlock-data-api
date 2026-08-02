import type { Context, Route } from "../router";
import { json, notFound } from "../respond";
import { NotFoundError, Storage } from "../storage";

export function versionsRoutes(storage: Storage): Route[] {
  return [
    {
      method: "GET",
      pattern: "/versions",
      handler: async (ctx: Context) => {
        const index = await storage.versionIndex();
        const builds = Object.values(index.builds ?? {}).sort((a, b) =>
          (b.captured_at ?? "").localeCompare(a.captured_at ?? ""),
        );
        return json({ count: builds.length, builds });
      },
    },
    {
      method: "GET",
      pattern: "/versions/:buildId/items",
      handler: async (ctx: Context) => {
        try {
          const data = await storage.archivedItems(ctx.params.buildId);
          return json(data);
        } catch (err) {
          if (err instanceof NotFoundError) return notFound(err.message);
          throw err;
        }
      },
    },
    {
      method: "GET",
      pattern: "/versions/:buildId/heroes",
      handler: async (ctx: Context) => {
        try {
          const data = await storage.archivedHeroes(ctx.params.buildId);
          return json(data);
        } catch (err) {
          if (err instanceof NotFoundError) return notFound(err.message);
          throw err;
        }
      },
    },
  ];
}
