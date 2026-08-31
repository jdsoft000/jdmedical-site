import { json } from "../lib/db.js";

export async function onRequest(context) {
  const { env } = context;

  return json({
    turnstileSiteKey: env.TURNSTILE_SITE_KEY || null,
  });
}
