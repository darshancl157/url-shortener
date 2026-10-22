# Static site headers (Render → web service → Settings → Headers)

Path: `/*`

| Name                      | Value                                                                                                                                                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Content-Security-Policy   | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'` |
| X-Frame-Options           | `DENY`                                                                                                                                                                                                                     |
| X-Content-Type-Options    | `nosniff`                                                                                                                                                                                                                  |
| Referrer-Policy           | `strict-origin-when-cross-origin`                                                                                                                                                                                          |
| Strict-Transport-Security | `max-age=31536000`                                                                                                                                                                                                         |
| Permissions-Policy        | `camera=(), microphone=(), geolocation=()`                                                                                                                                                                                 |

Apply to: url-shortener-web-uat, url-shortener-web-prod.
