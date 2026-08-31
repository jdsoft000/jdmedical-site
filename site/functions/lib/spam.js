const RATE_LIMIT_MAX = 5;
const RATE_LIMIT_WINDOW_HOURS = 1;
const MIN_SUBMIT_MS = 3000;
const MAX_SUBMIT_MS = 24 * 60 * 60 * 1000;

export function getClientIp(request) {
  return (
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("X-Forwarded-For")?.split(",")[0]?.trim() ||
    ""
  );
}

export async function hashIp(ip, env) {
  if (!ip) return "";
  const salt = env.RATE_LIMIT_SALT || "jdmedical-inquiry-rate";
  const data = new TextEncoder().encode(`${salt}:${ip}`);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function checkHoneypot(body) {
  if (body.website || body.company || body.url) {
    return { ok: false, code: "spam_detected" };
  }
  return { ok: true };
}

export function checkSubmitTiming(body) {
  const started = Number(body.form_started);
  if (!Number.isFinite(started) || started <= 0) {
    return { ok: false, code: "spam_timing" };
  }
  const elapsed = Date.now() - started;
  if (elapsed < MIN_SUBMIT_MS || elapsed > MAX_SUBMIT_MS) {
    return { ok: false, code: "spam_timing" };
  }
  return { ok: true };
}

export async function checkRateLimit(db, ipHash) {
  if (!ipHash) return { ok: true };

  const row = await db
    .prepare(
      `SELECT COUNT(*) AS count
       FROM post_rate_limits
       WHERE ip_hash = ? AND created_at > datetime('now', ?)`
    )
    .bind(ipHash, `-${RATE_LIMIT_WINDOW_HOURS} hours`)
    .first();

  if ((row?.count || 0) >= RATE_LIMIT_MAX) {
    return { ok: false, code: "rate_limited" };
  }
  return { ok: true };
}

export async function recordRateLimit(db, ipHash) {
  if (!ipHash) return;
  await db.prepare("INSERT INTO post_rate_limits (ip_hash) VALUES (?)").bind(ipHash).run();
  await db
    .prepare(
      `DELETE FROM post_rate_limits
       WHERE created_at < datetime('now', '-7 days')`
    )
    .run();
}

export async function verifyTurnstile(token, env, ip) {
  const secret = env.TURNSTILE_SECRET_KEY;
  if (!secret) return { ok: true };

  if (!token) {
    return { ok: false, code: "turnstile_required" };
  }

  const form = new FormData();
  form.append("secret", secret);
  form.append("response", token);
  if (ip) form.append("remoteip", ip);

  const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    return { ok: false, code: "turnstile_failed" };
  }

  const result = await response.json();
  if (!result.success) {
    return { ok: false, code: "turnstile_failed" };
  }

  return { ok: true };
}
