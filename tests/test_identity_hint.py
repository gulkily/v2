from __future__ import annotations

import unittest

from forum_web.identity_hint import (
    build_clear_identity_hint_cookie_header,
    build_identity_hint_cookie_value,
    build_set_identity_hint_cookie_header,
    validate_identity_hint_cookie_value,
)


class IdentityHintTests(unittest.TestCase):
    def test_cookie_value_round_trips_valid_fingerprint(self) -> None:
        cookie_value = build_identity_hint_cookie_value(
            "ABCD1234EF567890",
            secret="top-secret",
            now=100,
            max_age=60,
        )

        fingerprint = validate_identity_hint_cookie_value(
            cookie_value,
            secret="top-secret",
            now=120,
        )

        self.assertEqual(fingerprint, "abcd1234ef567890")

    def test_cookie_value_rejects_tampering(self) -> None:
        cookie_value = build_identity_hint_cookie_value(
            "ABCD1234EF567890",
            secret="top-secret",
            now=100,
            max_age=60,
        )
        tampered = cookie_value.replace("abcd1234ef567890", "ffff1234ef567890")

        fingerprint = validate_identity_hint_cookie_value(
            tampered,
            secret="top-secret",
            now=120,
        )

        self.assertIsNone(fingerprint)

    def test_cookie_value_rejects_expired_value(self) -> None:
        cookie_value = build_identity_hint_cookie_value(
            "ABCD1234EF567890",
            secret="top-secret",
            now=100,
            max_age=60,
        )

        fingerprint = validate_identity_hint_cookie_value(
            cookie_value,
            secret="top-secret",
            now=161,
        )

        self.assertIsNone(fingerprint)

    def test_set_cookie_header_contains_expected_flags(self) -> None:
        header = build_set_identity_hint_cookie_header(
            "ABCD1234EF567890",
            secret="top-secret",
            now=100,
            max_age=60,
        )

        self.assertIn("forum_identity_hint=", header)
        self.assertIn("Path=/", header)
        self.assertIn("Max-Age=60", header)
        self.assertIn("HttpOnly", header)
        self.assertIn("SameSite=Lax", header)
        self.assertIn("Secure", header)

    def test_clear_cookie_header_expires_cookie(self) -> None:
        header = build_clear_identity_hint_cookie_header()

        self.assertIn("forum_identity_hint=", header)
        self.assertIn("Max-Age=0", header)
        self.assertIn("expires=", header.lower())

    def test_cookie_headers_can_omit_secure_flag(self) -> None:
        set_header = build_set_identity_hint_cookie_header(
            "ABCD1234EF567890",
            secret="top-secret",
            secure=False,
        )
        clear_header = build_clear_identity_hint_cookie_header(secure=False)

        self.assertNotIn("Secure", set_header)
        self.assertNotIn("Secure", clear_header)


if __name__ == "__main__":
    unittest.main()
