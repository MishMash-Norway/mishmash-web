#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_page_git_meta import normalize_author, parse_git_log


class PageGitMetaTests(unittest.TestCase):
    def test_normalize_author_maps_github_actions(self):
        self.assertEqual(normalize_author("github-actions[bot]"), "GitHub Actions")
        self.assertEqual(normalize_author("Alex Anje"), "Alex Anje")

    def test_parse_git_log_maps_site_relative_paths(self):
        repo_root = Path(__file__).resolve().parents[1]
        site_root = repo_root / "site"
        if not (repo_root / ".git").exists():
            self.skipTest("not a git checkout")

        meta = parse_git_log(site_root, repo_root)
        self.assertTrue(meta)

        faq_key = "faq/index.md"
        if faq_key in meta:
            entry = meta[faq_key]
            self.assertIn("date", entry)
            self.assertIn("author", entry)
            self.assertTrue(entry["author"])


if __name__ == "__main__":
    unittest.main()
