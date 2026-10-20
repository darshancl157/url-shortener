"""Rate-limit rules in one place, so they're easy to review and tune."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Limit:
    limit: int
    window_seconds: int


LOGIN_PER_IP = Limit(20, 60)
LOGIN_PER_EMAIL_AND_IP = Limit(5, 60)
REGISTER_PER_IP = Limit(5, 3600)
REFRESH_PER_IP = Limit(30, 60)
SHORTEN_PER_USER = Limit(30, 60)
LIST_PER_USER = Limit(60, 60)
REDIRECT_PER_IP = Limit(300, 60)