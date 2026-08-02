import type { Context, Route } from "../router";
import { json, notFound } from "../respond";
import { Storage } from "../storage";
import type { Hero, HeroesData } from "../types";

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim().replace(/ +/g, "-");
}

function findHero(data: HeroesData, key: string): Hero | undefined {
  if (data.heroes[key]) return data.heroes[key];
  const numeric = Number(key);
  if (Number.isInteger(numeric)) {
    for (const hero of Object.values(data.heroes)) {
      if (hero.hero_id === numeric) return hero;
    }
  }
  const slug = slugify(key);
  for (const hero of Object.values(data.heroes)) {
    if (slugify(hero.display_name) === slug) return hero;
  }
  return undefined;
}

export function heroesRoutes(storage: Storage): Route[] {
  return [
    {
      method: "GET",
      pattern: "/heroes",
      handler: async (ctx: Context) => {
        const data = await storage.latestHeroes();
        return json(data);
      },
    },
    {
      method: "GET",
      pattern: "/heroes/ids",
      handler: async (ctx: Context) => {
        const data = await storage.latestHeroes();
        const ids: Record<string, { id: string; hero_id: number; display_name: string }> = {};
        for (const [id, hero] of Object.entries(data.heroes)) {
          ids[id] = { id, hero_id: hero.hero_id, display_name: hero.display_name };
        }
        return json(ids);
      },
    },
    {
      method: "GET",
      pattern: "/heroes/summary",
      handler: async (ctx: Context) => {
        const data = await storage.latestHeroes();
        const availableIn: Record<string, number> = {};
        let totalAbilities = 0;
        for (const hero of Object.values(data.heroes)) {
          const key = hero.available_in ?? "unknown";
          availableIn[key] = (availableIn[key] ?? 0) + 1;
          totalAbilities += Object.keys(hero.abilities ?? {}).length;
        }
        return json({ total: Object.keys(data.heroes).length, available_in: availableIn, total_abilities: totalAbilities });
      },
    },
    {
      method: "GET",
      pattern: "/heroes/:id",
      handler: async (ctx: Context) => {
        const data = await storage.latestHeroes();
        const hero = findHero(data, ctx.params.id);
        if (!hero) return notFound(`Hero '${ctx.params.id}' not found`);
        return json(hero);
      },
    },
  ];
}
