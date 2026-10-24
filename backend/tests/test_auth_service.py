import unittest
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import decode_access_token, hash_refresh_token
from app.services.auth_service import AuthService

SECRET = "test-secret-" + "x" * 40


class Clock:
    def __init__(self):
        self.t = datetime.now(timezone.utc)  # real time, so issued JWTs aren't already expired

    def __call__(self):
        return self.t


class FakeAuthRepo:
    """In-memory stand-in with the same behaviour as AuthRepository."""

    def __init__(self, clock):
        self.clock = clock
        self.users: dict[int, dict] = {}
        self.tokens: dict[str, dict] = {}

    def create_user(self, email, password_hash):
        if any(u["email"].lower() == email.lower() for u in self.users.values()):
            return None
        uid = len(self.users) + 1
        self.users[uid] = {"id": uid, "email": email, "password_hash": password_hash}
        return uid

    def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u["email"].lower() == email.lower()), None)

    def get_user(self, user_id):
        return self.users.get(user_id)

    def update_password_hash(self, user_id, password_hash):
        self.users[user_id]["password_hash"] = password_hash

    def insert_refresh_token(self, user_id, token_hash, family_id, expires_at):
        self.tokens[token_hash] = {"user_id": user_id, "family_id": family_id,
                                   "expires_at": expires_at, "revoked_at": None}

    def rotate_refresh_token(self, old_hash, new_hash, new_expires_at):
        t = self.tokens.get(old_hash)
        if t is None or t["revoked_at"] is not None or t["expires_at"] <= self.clock():
            return None
        t["revoked_at"] = self.clock()
        self.insert_refresh_token(t["user_id"], new_hash, t["family_id"], new_expires_at)
        return t["user_id"]

    def find_refresh_token(self, token_hash):
        return self.tokens.get(token_hash)

    def revoke_family(self, family_id):
        for t in self.tokens.values():
            if t["family_id"] == family_id and t["revoked_at"] is None:
                t["revoked_at"] = self.clock()


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.repo = FakeAuthRepo(self.clock)
        self.svc = AuthService(self.repo, Settings(database_url="x", jwt_secret=SECRET), now=self.clock)

    def login(self):
        self.svc.register("User@Example.com", "password123")
        return self.svc.login("user@example.com", "password123")

    # register
    def test_register_normalizes_email_and_hashes_password(self):
        uid = self.svc.register("  User@Example.COM ", "password123")
        user = self.repo.users[uid]
        self.assertEqual(user["email"], "user@example.com")
        self.assertNotEqual(user["password_hash"], "password123")

    def test_register_duplicate_email_is_case_insensitive(self):
        self.svc.register("a@b.com", "password123")
        with self.assertRaises(ConflictError):
            self.svc.register("A@B.COM", "password456")

    def test_register_validation(self):
        for email, pw in [("not-an-email", "password123"), ("a@b.com", "short"),
                          ("a@b.com", "x" * 129)]:
            with self.assertRaises(BadRequestError, msg=(email, pw)):
                self.svc.register(email, pw)

    # login
    def test_login_returns_access_token_for_user_and_stores_only_refresh_hash(self):
        pair = self.login()
        self.assertEqual(decode_access_token(pair.access_token, SECRET), 1)
        self.assertNotIn(pair.refresh_token, self.repo.tokens)
        self.assertIn(hash_refresh_token(pair.refresh_token), self.repo.tokens)

    def test_wrong_password_and_unknown_email_give_same_error(self):
        self.svc.register("a@b.com", "password123")
        with self.assertRaises(UnauthorizedError) as wrong_pw:
            self.svc.login("a@b.com", "nope-nope")
        with self.assertRaises(UnauthorizedError) as no_user:
            self.svc.login("nobody@b.com", "password123")
        self.assertEqual(wrong_pw.exception.message, no_user.exception.message)

    # refresh
    def test_refresh_rotates_token(self):
        first = self.login()
        second = self.svc.refresh(first.refresh_token)
        self.assertNotEqual(first.refresh_token, second.refresh_token)
        self.assertEqual(decode_access_token(second.access_token, SECRET), 1)
        third = self.svc.refresh(second.refresh_token)  # the new one works
        self.assertTrue(third.refresh_token)

    def test_reusing_old_token_revokes_whole_family(self):
        first = self.login()
        second = self.svc.refresh(first.refresh_token)
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(first.refresh_token)  # replay of a used token
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(second.refresh_token)  # legitimate token is now dead too

    def test_expired_refresh_token_rejected(self):
        pair = self.login()
        self.clock.t += timedelta(days=15)
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(pair.refresh_token)

    def test_missing_or_unknown_refresh_token_rejected(self):
        for token in [None, "", "made-up-token"]:
            with self.assertRaises(UnauthorizedError):
                self.svc.refresh(token)

    def test_other_sessions_survive_reuse_in_one_family(self):
        self.svc.register("user@example.com", "password123")
        laptop = self.svc.login("user@example.com", "password123")
        phone = self.svc.login("user@example.com", "password123")
        rotated = self.svc.refresh(laptop.refresh_token)
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(laptop.refresh_token)
        self.assertTrue(self.svc.refresh(phone.refresh_token).access_token)  # separate family
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(rotated.refresh_token)

    # logout
    def test_logout_revokes_session(self):
        pair = self.login()
        self.svc.logout(pair.refresh_token)
        with self.assertRaises(UnauthorizedError):
            self.svc.refresh(pair.refresh_token)

    def test_logout_without_token_is_harmless(self):
        self.svc.logout(None)
        self.svc.logout("unknown")

if __name__ == "__main__":
    unittest.main()