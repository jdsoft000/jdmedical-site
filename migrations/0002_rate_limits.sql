CREATE TABLE IF NOT EXISTS post_rate_limits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_post_rate_limits_ip_time ON post_rate_limits (ip_hash, created_at);
