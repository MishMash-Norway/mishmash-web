"""The Python tokenizer for the chat knowledge base matches the shared cases.

The JavaScript side checks itself against the same file
(scripts/eval_chat_retrieval.mjs), so the two cannot drift apart unnoticed.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_knowledge_base as kb

CASES = Path(__file__).resolve().parents[1] / "tests" / "chat" / "tokenizer-cases.json"


class TokenizerTest(unittest.TestCase):
    def test_shared_cases(self):
        for case in json.loads(CASES.read_text(encoding="utf-8"))["cases"]:
            self.assertEqual(kb.tokenize(case["in"]), case["out"], case["in"])

    def test_work_package_shorthand_is_one_word(self):
        self.assertEqual(kb.normalise("Work Package 4"), "wp4")
        self.assertEqual(kb.normalise("arbeidspakke 2"), "wp2")
        self.assertEqual(kb.normalise("wp 6"), "wp6")

    def test_a_page_keeps_its_own_words(self):
        self.assertIn("kunstsilo", kb.tokenize("The conference was at Kunstsilo."))


if __name__ == "__main__":
    unittest.main()
