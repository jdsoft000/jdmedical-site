import { isAdminPassword, verifyPassword } from "../../lib/crypto.js";
import { ensureSchema, json } from "../../lib/db.js";

export async function onRequest(context) {
  const { request, env, params } = context;
  const id = Number(params.id);

  if (!Number.isInteger(id) || id < 1) {
    return json({ error: "invalid_id" }, 400);
  }

  if (!env.DB) {
    return json({ error: "database_unavailable" }, 503);
  }

  await ensureSchema(env.DB);

  const row = await env.DB.prepare(
    `SELECT id, name, title, contact, content, is_secret, password_hash, created_at
     FROM inquiries
     WHERE id = ?`
  )
    .bind(id)
    .first();

  if (!row) {
    return json({ error: "not_found" }, 404);
  }

  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid_json" }, 400);
    }

    const password = typeof body.password === "string" ? body.password.trim() : "";
    if (!password) {
      return json({ error: "password_required" }, 400);
    }

    if (!row.is_secret) {
      return json({
        item: {
          id: row.id,
          name: row.name,
          title: row.title,
          contact: row.contact,
          content: row.content,
          is_secret: false,
          created_at: row.created_at,
        },
      });
    }

    const allowed =
      isAdminPassword(env, password) ||
      (await verifyPassword(password, row.password_hash));

    if (!allowed) {
      return json({ error: "invalid_password" }, 403);
    }

    return json({
      item: {
        id: row.id,
        name: row.name,
        title: row.title,
        contact: row.contact,
        content: row.content,
        is_secret: true,
        created_at: row.created_at,
      },
    });
  }

  if (request.method === "DELETE") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid_json" }, 400);
    }

    const password = typeof body.password === "string" ? body.password.trim() : "";
    if (!isAdminPassword(env, password)) {
      return json({ error: "forbidden" }, 403);
    }

    await env.DB.prepare("DELETE FROM inquiries WHERE id = ?").bind(id).run();
    return json({ ok: true });
  }

  return json({ error: "method_not_allowed" }, 405);
}
