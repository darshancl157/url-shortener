import unittest
from datetime import datetime, timedelta, timezone

import jwt

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)

SECRET = "test-secret-" + "x" * 40
TTL = timedelta(minutes=15)


class PasswordTests(unittest.TestCase):
    def test_hash_is_not_the_password_and_verifies(self):
        h = hash_password("correct horse battery staple")
        self.assertNotIn("correct horse", h)
        self.assertTrue(h.startswith("$argon2id$"))
        self.assertTrue(verify_password(h, "correct horse battery staple"))

    def test_wrong_password_fails(self):
        self.assertFalse(verify_password(hash_password("right"), "wrong"))

    def test_same_password_gives_different_hashes(self):
        self.assertNotEqual(hash_password("same"), hash_password("same"))  # random salt

    def test_garbage_hash_fails_instead_of_crashing(self):
        self.assertFalse(verify_password("not-a-hash", "anything"))


class AccessTokenTests(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(decode_access_token(create_access_token(42, SECRET, TTL), SECRET), 42)

    def test_expired_token_rejected(self):
        old = datetime.now(timezone.utc) - timedelta(hours=1)
        with self.assertRaises(UnauthorizedError):
            decode_access_token(create_access_token(42, SECRET, TTL, now=old), SECRET)

    def test_wrong_secret_rejected(self):
        with self.assertRaises(UnauthorizedError):
            decode_access_token(create_access_token(42, SECRET, TTL), "other-" + "y" * 40)

    def test_tampered_token_rejected(self):
        token = create_access_token(42, SECRET, TTL)
        with self.assertRaises(UnauthorizedError):
            decode_access_token(token[:-2] + ("AA" if token[-2:] != "AA" else "BB"), SECRET)

    def test_non_access_token_rejected(self):
        now = datetime.now(timezone.utc)
        other = jwt.encode(
            {"sub": "42", "type": "refresh", "iat": now, "exp": now + TTL}, SECRET, algorithm="HS256"
        )
        with self.assertRaises(UnauthorizedError):
            decode_access_token(other, SECRET)

    def test_unsigned_token_rejected(self):
        now = datetime.now(timezone.utc)
        unsigned = jwt.encode(
            {"sub": "42", "type": "access", "iat": now, "exp": now + TTL}, None, algorithm="none"
        )
        with self.assertRaises(UnauthorizedError):
            decode_access_token(unsigned, SECRET)


class RefreshTokenTests(unittest.TestCase):
    def test_tokens_are_random_and_long(self):
        a, b = new_refresh_token(), new_refresh_token()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 40)

    def test_hash_is_stable_and_not_the_token(self):
        t = new_refresh_token()
        self.assertEqual(hash_refresh_token(t), hash_refresh_token(t))
        self.assertNotEqual(hash_refresh_token(t), t)
        self.assertEqual(len(hash_refresh_token(t)), 64)