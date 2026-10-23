from starlette.requests import Request

from app.api.deps import client_ip


def make_request(headers=None, client=("10.0.0.1", 1234)):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw, "client": client})


def test_uses_configured_header_over_forwarded_for():
    req = make_request({"CF-Connecting-IP": "223.181.57.123", "X-Forwarded-For": "203.0.113.7"})
    assert client_ip(req, header="cf-connecting-ip") == "223.181.57.123"


def test_ignores_header_when_not_configured():
    req = make_request({"CF-Connecting-IP": "198.51.100.9"})
    assert client_ip(req, header="") == "10.0.0.1"


def test_falls_back_when_header_missing_or_not_an_ip():
    assert client_ip(make_request(), header="cf-connecting-ip") == "10.0.0.1"
    req = make_request({"CF-Connecting-IP": "not-an-ip"})
    assert client_ip(req, header="cf-connecting-ip") == "10.0.0.1"


def test_unknown_without_client():
    assert client_ip(make_request(client=None), header="") == "unknown"