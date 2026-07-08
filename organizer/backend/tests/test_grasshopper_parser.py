import email
import unittest

from app.services.grasshopper_parser import is_grasshopper_email, parse_grasshopper_email


class GrasshopperParserTests(unittest.TestCase):
    def test_detects_grasshopper_voicemail_email(self) -> None:
        raw = """From: notifications@grasshopper.com
To: you@example.com
Subject: Voicemail from (555) 123-4567
Message-ID: <gh-test-1@grasshopper.com>
Date: Tue, 08 Jul 2026 14:00:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Please call me back about the kitchen project.
"""
        message = email.message_from_string(raw)
        self.assertTrue(is_grasshopper_email(message))
        event = parse_grasshopper_email(message)
        assert event is not None
        self.assertEqual(event.event_type, "voicemail")
        self.assertEqual(event.phone_number, "(555) 123-4567")
        self.assertIn("kitchen project", event.transcript or "")

    def test_ignores_unrelated_email(self) -> None:
        raw = """From: newsletter@example.com
To: you@example.com
Subject: Weekly newsletter
Message-ID: <news-1@example.com>
Date: Tue, 08 Jul 2026 14:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Hello there.
"""
        message = email.message_from_string(raw)
        self.assertFalse(is_grasshopper_email(message))
        self.assertIsNone(parse_grasshopper_email(message))


if __name__ == "__main__":
    unittest.main()
