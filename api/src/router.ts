import type { Env } from "./env";
import { notFound } from "./respond";

export interface Context {
  env: Env;
  request: Request;
  params: Record<string, string>;
}

export type Handler = (ctx: Context) => Response | Promise<Response>;

export interface Route {
  method: string;
  pattern: string;
  handler: Handler;
}

export class Router {
  readonly routes: Route[] = [];

  addAll(routes: Route[]): void {
    this.routes.push(...routes);
  }

  handle(request: Request, env: Env): Response | Promise<Response> {
    const url = new URL(request.url);
    const segments = url.pathname.split("/").filter(Boolean);

    let best: { route: Route; params: Record<string, string> } | undefined;
    let bestScore = -1;

    for (const route of this.routes) {
      if (route.method !== request.method) continue;

      const patternSegments = route.pattern.split("/").filter(Boolean);
      if (patternSegments.length !== segments.length) continue;

      const params: Record<string, string> = {};
      let score = 0;
      let matched = true;

      for (let i = 0; i < patternSegments.length; i++) {
        const patternSegment = patternSegments[i];
        if (patternSegment.startsWith(":")) {
          params[patternSegment.slice(1)] = decodeURIComponent(segments[i]);
        } else if (patternSegment === segments[i]) {
          score += 2;
        } else {
          matched = false;
          break;
        }
      }

      if (matched && score > bestScore) {
        best = { route, params };
        bestScore = score;
      }
    }

    if (!best) return notFound();
    return best.route.handler({ env, request, params: best.params });
  }
}
