import email
import unittest

from app.services.email_imap import parse_mailbox_email
from app.services.grasshopper_parser import is_grasshopper_email


class EmailImapTests(unittest.TestCase):
    def test_parses_regular_email(self) -> None:
        raw = """From: client@example.com
To: you@company.com
Subject: Project update
Message-ID: <mail-1@example.com>
Date: Tue, 08 Jul 2026 14:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Please review the attached timeline.
"""
        message = email.message_from_string(raw)
        parsed = parse_mailbox_email(message, "work", "you@company.com")
        assert parsed is not None
        self.assertEqual(parsed.account_label, "work")
        self.assertEqual(parsed.from_address, "client@example.com")
        self.assertIn("timeline", parsed.body)

    def test_skips_grasshopper_voicemail_email(self) -> None:
        raw = """From: notifications@grasshopper.com
To: you@company.com
Subject: Voicemail from (555) 123-4567
Message-ID: <gh-1@grasshopper.com>
Date: Tue, 08 Jul 2026 14:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Please call me back.
"""
        message = email.message_from_string(raw)
        self.assertTrue(is_grasshopper_email(message))
        self.assertIsNone(parse_mailbox_email(message, "work", "you@company.com"))


if __name__ == "__main__":
    unittest.main()
