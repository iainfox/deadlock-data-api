import type { Context, Route } from "../router";
import { json, notFound } from "../respond";
import { Storage } from "../storage";
import type { Item, ItemsData } from "../types";

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim().replace(/ +/g, "-");
}

function findItem(data: ItemsData, key: string): Item | undefined {
  if (data.items[key]) return data.items[key];
  const slug = slugify(key);
  for (const item of Object.values(data.items)) {
    if (slugify(item.display_name) === slug) return item;
  }
  return undefined;
}

export function itemsRoutes(storage: Storage): Route[] {
  return [
    {
      method: "GET",
      pattern: "/items",
      handler: async (ctx: Context) => {
        const data = await storage.latestItems();
        return json(data);
      },
    },
    {
      method: "GET",
      pattern: "/items/ids",
      handler: async (ctx: Context) => {
        const data = await storage.latestItems();
        const ids: Record<string, { id: string; display_name: string; tier: number }> = {};
        for (const [id, item] of Object.entries(data.items)) {
          ids[id] = { id, display_name: item.display_name, tier: item.tier };
        }
        return json(ids);
      },
    },
    {
      method: "GET",
      pattern: "/items/summary",
      handler: async (ctx: Context) => {
        const data = await storage.latestItems();
        const tiers: Record<string, number> = {};
        const slots: Record<string, number> = {};
        const activations: Record<string, number> = {};
        for (const item of Object.values(data.items)) {
          tiers[item.tier] = (tiers[item.tier] ?? 0) + 1;
          slots[item.slot] = (slots[item.slot] ?? 0) + 1;
          activations[item.activation] = (activations[item.activation] ?? 0) + 1;
        }
        return json({
          total: Object.keys(data.items).length,
          tiers,
          slots,
          activations,
        });
      },
    },
    {
      method: "GET",
      pattern: "/items/:id",
      handler: async (ctx: Context) => {
        const data = await storage.latestItems();
        const item = findItem(data, ctx.params.id);
        if (!item) return notFound(`Item '${ctx.params.id}' not found`);
        return json(item);
      },
    },
  ];
}
