import { hashPassword } from "../lib/crypto.js";
import { ensureSchema, json, trimText } from "../lib/db.js";
import {
  checkHoneypot,
  checkRateLimit,
  checkSubmitTiming,
  getClientIp,
  hashIp,
  recordRateLimit,
  verifyTurnstile,
} from "../lib/spam.js";

export async function onRequest(context) {
  const { request, env } = context;
  if (!env.DB) {
    return json({ error: "database_unavailable" }, 503);
  }

  await ensureSchema(env.DB);

  if (request.method === "GET") {
    const result = await env.DB.prepare(
      `SELECT id, name, title, contact, content, is_secret, created_at
       FROM inquiries
       ORDER BY id DESC`
    ).all();

    const items = (result.results || []).map((row) => {
      const base = {
        id: row.id,
        name: row.name,
        title: row.title,
        is_secret: Boolean(row.is_secret),
        created_at: row.created_at,
      };
      if (row.is_secret) return base;
      return {
        ...base,
        contact: row.contact,
        content: row.content,
      };
    });

    return json({ items });
  }

  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid_json" }, 400);
    }

    const honeypot = checkHoneypot(body);
    if (!honeypot.ok) {
      return json({ ok: true });
    }

    const timing = checkSubmitTiming(body);
    if (!timing.ok) {
      return json({ error: timing.code }, 429);
    }

    const clientIp = getClientIp(request);
    const ipHash = await hashIp(clientIp, env);
    const rate = await checkRateLimit(env.DB, ipHash);
    if (!rate.ok) {
      return json({ error: rate.code }, 429);
    }

    const turnstile = await verifyTurnstile(body.turnstile_token, env, clientIp);
    if (!turnstile.ok) {
      return json({ error: turnstile.code }, 403);
    }

    const name = trimText(body.name, 40);
    const title = trimText(body.title, 100);
    const contact = trimText(body.contact, 80);
    const content = trimText(body.content, 300);
    const isSecret = Boolean(body.is_secret);
    const password = typeof body.password === "string" ? body.password.trim() : "";

    if (!name || !title || !contact || !content) {
      return json({ error: "missing_fields" }, 400);
    }

    if (content.length > 300) {
      return json({ error: "content_too_long" }, 400);
    }

    if (isSecret) {
      if (password.length < 4 || password.length > 32) {
        return json({ error: "invalid_password" }, 400);
      }
    }

    const passwordHash = isSecret ? await hashPassword(password) : null;

    const insert = await env.DB.prepare(
      `INSERT INTO inquiries (name, title, contact, content, is_secret, password_hash)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(name, title, contact, content, isSecret ? 1 : 0, passwordHash)
      .run();

    await recordRateLimit(env.DB, ipHash);

    return json({ ok: true, id: insert.meta.last_row_id }, 201);
  }

  return json({ error: "method_not_allowed" }, 405);
}
