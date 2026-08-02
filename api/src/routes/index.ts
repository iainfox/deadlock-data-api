import type { Context, Route } from "../router";
import { json } from "../respond";
import { Storage } from "../storage";
import { heroesRoutes } from "./heroes";
import { itemsRoutes } from "./items";
import { versionsRoutes } from "./versions";

export function buildRoutes(storage: Storage): Route[] {
  return [
    {
      method: "GET",
      pattern: "/",
      handler: async (ctx: Context) => {
        const index = await storage.versionIndex();
        const builds = Object.values(index.builds ?? {});
        const metadata = await storage.latestItems();
        return json({
          name: "deadlock-data-api",
          endpoints: {
            items: "/items",
            items_ids: "/items/ids",
            items_summary: "/items/summary",
            item_by_id_or_name: "/items/:id",
            heroes: "/heroes",
            heroes_ids: "/heroes/ids",
            heroes_summary: "/heroes/summary",
            hero_by_id_or_name: "/heroes/:id",
            versions: "/versions",
            version_items: "/versions/:buildId/items",
            version_heroes: "/versions/:buildId/heroes",
          },
          versions: {
            count: builds.length,
            latest_build: metadata._metadata?.build_id ?? null,
            captured_at: metadata._metadata?.captured_at ?? null,
          },
        });
      },
    },
    ...itemsRoutes(storage),
    ...heroesRoutes(storage),
    ...versionsRoutes(storage),
  ];
}
