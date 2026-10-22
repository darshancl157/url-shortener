"""Security headers added to every API response."""

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000",
    "Cross-Origin-Opener-Policy": "same-origin",
}

# The API only returns JSON and redirects, never pages, so it needs no scripts, styles or images.
API_CSP = "default-src 'none'; frame-ancestors 'none'"

# Swagger UI and ReDoc load scripts from a CDN and use inline scripts, so a strict CSP would break them.
DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc"})


def security_headers_for(path: str) -> dict[str, str]:
    headers = dict(BASE_HEADERS)
    if path not in DOCS_PATHS:
        headers["Content-Security-Policy"] = API_CSP
    return headers