#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_ai_colophon_stats import parse_recent_commit_log


class AiColophonStatsTests(unittest.TestCase):
    def test_parse_recent_commit_log_handles_separator_chars_in_message(self):
        log = (
            "sha1\x002026-08-07\x00Alice\x00Subject with \x1e and \x1f markers\x00"
            "Body line 1\nCo-Authored-By: Copilot <bot@example.com>\n"
            "Body with \x1e and \x1f markers\x00"
            "sha2\x002026-08-06\x00github-actions[bot]\x00Automated update\x00\x00"
        )

        self.assertEqual(
            parse_recent_commit_log(log),
            [
                {
                    "date": "2026-08-07",
                    "subject": "Subject with \x1e and \x1f markers",
                    "how": "ai_assisted",
                },
                {
                    "date": "2026-08-06",
                    "subject": "Automated update",
                    "how": "automated",
                },
            ],
        )

    def test_parse_recent_commit_log_rejects_malformed_payload(self):
        with self.assertRaisesRegex(ValueError, "Malformed git log payload"):
            parse_recent_commit_log("sha\x002026-08-07\x00Alice\x00Subject only")


if __name__ == "__main__":
    unittest.main()
