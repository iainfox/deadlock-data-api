export interface Metadata {
  source?: string;
  count?: number;
  pricing?: number[];
  build_id?: string;
  captured_at?: string;
  manifests?: Record<string, string>;
}

export interface ItemStat {
  value: number | string;
  usage?: string;
}

export interface Item {
  id: string;
  display_name: string;
  description: string;
  tier: number;
  soul_cost: number;
  slot: string;
  activation: string;
  available_in: string;
  stats: Record<string, ItemStat>;
  passive: Record<string, number | string>;
  active: Record<string, number | string>;
  components?: string[];
  upgrades?: Record<string, unknown>[];
  tooltip_descriptions?: { section: string; description: string }[];
  [key: string]: unknown;
}

export interface ItemsData {
  _metadata: Metadata;
  items: Record<string, Item>;
}

export interface Ability {
  id: string;
  display_name: string;
  description: string;
  activation: string;
  stats: Record<string, ItemStat>;
  [key: string]: unknown;
}

export interface Hero {
  id: string;
  display_name: string;
  description: string;
  hero_id: number;
  complexity: number;
  available_in: string;
  stats: Record<string, number | string>;
  stat_scaling: Record<string, number | string>;
  tags: string[];
  scaling_stats?: Record<string, number | string>;
  weapon?: Ability;
  abilities?: Record<string, Ability>;
  [key: string]: unknown;
}

export interface HeroesData {
  _metadata: Metadata;
  heroes: Record<string, Hero>;
}

export interface VersionEntry {
  build_id: string;
  captured_at: string;
  manifests: Record<string, string>;
  items_count?: number;
  heroes_count?: number;
  items_hash?: string;
  heroes_hash?: string;
}

export interface VersionIndex {
  builds: Record<string, VersionEntry>;
}
