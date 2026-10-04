import unittest
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.core.exceptions import BadRequestError, ConflictError, IdGenerationError, NotFoundError
from app.services.url_service import UrlService


class FakeRepo:
    def __init__(self):
        self.rows: dict[str, dict] = {}
        self.always_conflict = False

    def insert(self, short_id, long_url, expires_at):
        if self.always_conflict or short_id in self.rows:
            return False
        self.rows[short_id] = {"long_url": long_url, "clicks": 0}
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

    def test_shorten_generates_id_of_configured_length(self):
        short_id, url = self.svc.shorten("https://example.com/a", None, None)
        self.assertEqual(len(short_id), 6)
        self.assertEqual(url, "https://example.com/a")
        self.assertIn(short_id, self.repo.rows)

    def test_rejects_bad_urls(self):
        for bad in ["", "ftp://x.com", "example.com", "http://", "https://" + "a" * 3000]:
            with self.assertRaises(BadRequestError, msg=bad):
                self.svc.shorten(bad, None, None)

    def test_custom_alias_ok_and_conflict(self):
        self.assertEqual(self.svc.shorten("https://a.com", "my-link", None)[0], "my-link")
        with self.assertRaises(ConflictError):
            self.svc.shorten("https://b.com", "my-link", None)

    def test_custom_alias_validation(self):
        for bad in ["ab", "x" * 11, "has space", "API", "health"]:
            with self.assertRaises(BadRequestError, msg=bad):
                self.svc.shorten("https://a.com", bad, None)

    def test_expiry_rules(self):
        with self.assertRaises(BadRequestError):
            self.svc.shorten("https://a.com", None, datetime.now())  # naive
        with self.assertRaises(BadRequestError):
            self.svc.shorten("https://a.com", None, datetime.now(timezone.utc) - timedelta(hours=1))
        self.svc.shorten("https://a.com", None, datetime.now(timezone.utc) + timedelta(hours=1))

    def test_id_generation_gives_up(self):
        self.repo.always_conflict = True
        with self.assertRaises(IdGenerationError):
            self.svc.shorten("https://a.com", None, None)

    def test_resolve_and_stats(self):
        short_id, _ = self.svc.shorten("https://a.com", None, None)
        self.assertEqual(self.svc.resolve(short_id), "https://a.com")
        self.assertEqual(self.svc.stats(short_id)["clicks"], 1)
        with self.assertRaises(NotFoundError):
            self.svc.resolve("nope")
        with self.assertRaises(NotFoundError):
            self.svc.stats("nope")


if __name__ == "__main__":
    unittest.main()