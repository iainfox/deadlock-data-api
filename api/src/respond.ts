export function json(data: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=300",
      ...headers,
    },
  });
}

export function notFound(message = "Not found"): Response {
  return json({ error: message }, 404, { "Cache-Control": "no-store" });
}

export function serverError(message = "Internal server error"): Response {
  return json({ error: message }, 500, { "Cache-Control": "no-store" });
}

export const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "*",
};

export function preflight(): Response {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}
