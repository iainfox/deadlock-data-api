import type { Env } from "./env";
import { preflight } from "./respond";
import { Router } from "./router";
import { buildRoutes } from "./routes";
import { Storage } from "./storage";

const router = new Router();

function initRouter(env: Env): void {
  if (router.routes.length === 0) {
    router.addAll(buildRoutes(Storage.fromEnv(env)));
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    initRouter(env);

    if (request.method === "OPTIONS") return preflight();
    if (request.method !== "GET") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json; charset=utf-8" },
      });
    }

    return router.handle(request, env);
  },
};
