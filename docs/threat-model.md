# Threat model — release 1.2.0

## What we protect

| Asset                                | Why it matters                                          |
| ------------------------------------ | ------------------------------------------------------- |
| User accounts (email, password hash) | Takeover lets an attacker create/view links as the user |
| Refresh tokens                       | A stolen token = a 14-day session                       |
| `JWT_SECRET`                         | Anyone holding it can mint access tokens for any user   |
| Database credentials (app, migrator) | Migrator can drop tables; app can read all data         |
| Render deploy hooks                  | Anyone holding one can redeploy a service               |
| The short domain's reputation        | Abuse (phishing links) gets the domain blocklisted      |

## Who might attack

- Anonymous internet users: scraping links, brute-forcing logins, mass sign-ups, phishing via short links
- A logged-in user trying to read or change other users' links
- Supply chain: a compromised or vulnerable dependency
- Leaked secrets: through logs, chat or a laptop

## Trust boundaries

Browser → Render static site (rewrites `/api/*`) → Render API → Neon Postgres.
GitHub Actions → Neon (migrator) and Render (deploy hooks).

## Threats and controls

| #   | Threat                                                      | Control                                                                                                | Status                            |
| --- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------- |
| T1  | Password brute force / credential stuffing                  | Argon2id; rate limits 20/min per IP and 5/min per email+IP                                             | Done                              |
| T2  | Account enumeration via login                               | Same error and equalised timing for unknown email or wrong password                                    | Done                              |
| T3  | Account enumeration via register (409 on an existing email) | Register limited to 5/hour per IP                                                                      | **Accepted**                      |
| T4  | Stolen refresh token reused                                 | Rotation; reuse detection revokes the whole family; only the SHA-256 is stored                         | Done                              |
| T5  | XSS steals the access token                                 | Token only in JS memory, 15-minute TTL; strict CSP (`script-src 'self'`)                               | Done                              |
| T6  | CSRF on the refresh endpoint                                | Cookie is HttpOnly, Secure, SameSite=Strict, Path=/api/auth; same-origin proxy                         | Done                              |
| T7  | Clickjacking                                                | `frame-ancestors 'none'` and `X-Frame-Options: DENY` on site and API                                   | Done                              |
| T8  | User A reads user B's links or stats                        | Owner check in the service; another user's link returns 404, not 403                                   | Done                              |
| T9  | Short links used for phishing or malware                    | None yet (Safe Browsing planned)                                                                       | **Accepted**                      |
| T10 | Links pointing at our own domain (loops) or private IPs     | None (S3 skipped); the server never fetches the target                                                 | **Accepted**                      |
| T11 | Scraping or flooding the redirect                           | 300/min per IP                                                                                         | Done; see V1                      |
| T12 | Vulnerable dependency                                       | pip-audit and npm audit in CI; Dependabot weekly                                                       | Done                              |
| T13 | SQL injection                                               | Every query uses bound parameters via `text()`; no string formatting                                   | Done                              |
| T14 | App compromise deletes data                                 | App role has no DELETE; only the migrator owns the schema                                              | Done                              |
| T15 | Unreviewed code reaches prod                                | Ruleset: PRs, 3 required checks, no bypass; prod environment needs approval                            | Done (prod in P3)                 |
| T16 | Secret leak                                                 | Hooks and DB URLs in GitHub Secrets only; per-environment `JWT_SECRET`; `.env` holds only the app role | Done; one leaked hook was rotated |
| T17 | Mass sign-ups with fake emails                              | No email verification; register rate limit only                                                        | **Accepted**                      |
| T18 | Rate-limit counters reset on restart or differ per process  | In-memory limiter behind a `RateLimiter` interface; swap for Redis later                               | **Accepted**                      |
| T19 | `refresh_tokens` grows forever                              | None yet                                                                                               | **Accepted** (cleanup job later)  |
| T20 | `/docs` exposes the API surface in prod                     | Decide in P2                                                                                           | Open                              |
| T21 | Denial of service on the free tier                          | None (no WAF or edge layer)                                                                            | **Accepted**                      |

## To verify in UAT (release 1.2.0)

- **V1: what does the API see as the client IP?**
  - Through the site, all users may share one Render proxy IP. If so, every user shares one login bucket and 20 logins/min becomes a global limit.
  - The uvicorn start command's `--forwarded-allow-ips` decides this.
- **V2: can `X-Forwarded-For` be spoofed to dodge IP limits?**
- **V3: no CSP violations in the browser console** (login, shorten, the grid, copy).
- **V4: headers appear on API and site responses;** check for duplicates through the `/api` rewrite.

## Out of scope for this release

OAuth, Safe Browsing, URL target validation (S3), edge or WAF, Redis-backed limits, audit logging.
