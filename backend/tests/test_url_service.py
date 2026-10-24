import itertools
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
        self._clock = itertools.count()  # strictly increasing "created_at"

    def insert(self, short_id, long_url, expires_at, user_id):
        if self.always_conflict or short_id in self.rows:
            return False
        self.rows[short_id] = {"short_id": short_id, "long_url": long_url, "clicks": 0,
                               "user_id": user_id, "created_at": next(self._clock)}
        return True

    def hit(self, short_id):
        row = self.rows.get(short_id)
        if not row:
            return None
        row["clicks"] += 1
        return row["long_url"]

    def stats(self, short_id):
        return self.rows.get(short_id)

    def list_by_user(self, user_id, limit, offset):
        mine = sorted((r for r in self.rows.values() if r["user_id"] == user_id),
                      key=lambda r: r["created_at"], reverse=True)
        return mine[offset:offset + limit], len(mine)


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

    def test_list_urls_returns_only_callers_links_newest_first(self):
        first, _ = self.shorten("https://a.com")
        self.shorten("https://other.com", user_id=OTHER)
        second, _ = self.shorten("https://b.com")
        rows, total = self.svc.list_urls(OWNER, limit=10, offset=0)
        self.assertEqual([r["short_id"] for r in rows], [second, first])
        self.assertEqual(total, 2)

    def test_list_urls_pages(self):
        ids = [self.shorten(f"https://{i}.com")[0] for i in range(5)]
        page, total = self.svc.list_urls(OWNER, limit=2, offset=2)
        self.assertEqual([r["short_id"] for r in page], [ids[2], ids[1]])
        self.assertEqual(total, 5)

    def test_list_urls_validates_paging(self):
        for limit, offset in [(0, 0), (101, 0), (10, -1)]:
            with self.assertRaises(BadRequestError, msg=(limit, offset)):
                self.svc.list_urls(OWNER, limit=limit, offset=offset)


if __name__ == "__main__":
    unittest.main()