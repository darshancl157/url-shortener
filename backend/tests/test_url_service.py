import unittest
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.core.exceptions import BadRequestError, ConflictError, IdGenerationError, NotFoundError
from app.services.url_service import UrlService

OWNER, OTHER = 1, 2


class FakeRepo:
    def __init__(self):
        self.rows: dict[str, dict] = {}
        self.always_conflict = False

    def insert(self, short_id, long_url, expires_at, user_id):
        if self.always_conflict or short_id in self.rows:
            return False
        self.rows[short_id] = {"long_url": long_url, "clicks": 0, "user_id": user_id}
        return True

    def hit(self, short_id):
        row = self.rows.get(short_id)
        if not row:
            return None
        row["clicks"] += 1
        return row["long_url"]

    def stats(self, short_id):
        return self.rows.get(short_id)


class UrlServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = FakeRepo()
        self.svc = UrlService(self.repo, Settings(database_url="x"))

    def shorten(self, url, alias=None, expires_at=None, user_id=OWNER):
        return self.svc.shorten(url, alias, expires_at, user_id)

    def test_shorten_generates_id_of_configured_length_and_records_owner(self):
        short_id, url = self.shorten("https://example.com/a")
        self.assertEqual(len(short_id), 6)
        self.assertEqual(url, "https://example.com/a")
        self.assertEqual(self.repo.rows[short_id]["user_id"], OWNER)

    def test_rejects_bad_urls(self):
        for bad in ["", "ftp://x.com", "example.com", "http://", "https://" + "a" * 3000]:
            with self.assertRaises(BadRequestError, msg=bad):
                self.shorten(bad)

    def test_custom_alias_ok_and_conflict(self):
        self.assertEqual(self.shorten("https://a.com", "my-link")[0], "my-link")
        with self.assertRaises(ConflictError):
            self.shorten("https://b.com", "my-link", user_id=OTHER)

    def test_custom_alias_validation(self):
        for bad in ["ab", "x" * 11, "has space", "API", "health"]:
            with self.assertRaises(BadRequestError, msg=bad):
                self.shorten("https://a.com", bad)

    def test_expiry_rules(self):
        with self.assertRaises(BadRequestError):
            self.shorten("https://a.com", expires_at=datetime.now())  # naive
        with self.assertRaises(BadRequestError):
            self.shorten("https://a.com", expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        self.shorten("https://a.com", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

    def test_id_generation_gives_up(self):
        self.repo.always_conflict = True
        with self.assertRaises(IdGenerationError):
            self.shorten("https://a.com")

    def test_resolve_is_public_and_stats_are_owner_only(self):
        short_id, _ = self.shorten("https://a.com")
        self.assertEqual(self.svc.resolve(short_id), "https://a.com")
        self.assertEqual(self.svc.stats(short_id, OWNER)["clicks"], 1)
        with self.assertRaises(NotFoundError):
            self.svc.stats(short_id, OTHER)  # another user's link looks missing
        with self.assertRaises(NotFoundError):
            self.svc.resolve("nope")
        with self.assertRaises(NotFoundError):
            self.svc.stats("nope", OWNER)


if __name__ == "__main__":
    unittest.main()