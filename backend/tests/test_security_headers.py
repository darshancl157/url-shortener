from app.core.security_headers import API_CSP, security_headers_for


def test_api_paths_get_strict_csp():
    headers = security_headers_for("/api/urls")
    assert headers["Content-Security-Policy"] == API_CSP
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"


def test_redirect_path_gets_headers():
    headers = security_headers_for("/abc123")
    assert headers["Content-Security-Policy"] == API_CSP
    assert headers["Referrer-Policy"] == "no-referrer"


def test_docs_skip_csp_but_keep_other_headers():
    headers = security_headers_for("/docs")
    assert "Content-Security-Policy" not in headers
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_returns_independent_copy():
    security_headers_for("/api/urls")["X-Frame-Options"] = "changed"
    assert security_headers_for("/api/urls")["X-Frame-Options"] == "DENY"