#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tag_merge import (
    apply_to_frontmatter,
    apply_to_tag_groups,
    build_lookup,
    merge_tag_list,
    suggest_merge_yaml,
)


class TagMergeTests(unittest.TestCase):
    def test_build_lookup_merges_variants(self):
        lookup = build_lookup(
            {
                "merges": {
                    "Artificial intelligence": [
                        "Artificial Intelligence",
                        "artificial intelligence",
                        "AI",
                    ]
                },
                "aliases": {"Digital libary": "Digital library"},
            }
        )
        self.assertEqual(lookup["Artificial Intelligence"], "Artificial intelligence")
        self.assertEqual(lookup["Artificial intelligence"], "Artificial intelligence")
        self.assertEqual(lookup["AI"], "Artificial intelligence")
        self.assertEqual(lookup["Digital libary"], "Digital library")

    def test_merge_tag_list_deduplicates_after_mapping(self):
        lookup = build_lookup(
            {
                "merges": {
                    "Machine Learning": ["Machine learning", "machine learning"],
                }
            }
        )
        self.assertEqual(
            merge_tag_list(
                ["Machine learning", "machine learning", "Robotics"],
                lookup,
            ),
            ["Machine Learning", "Robotics"],
        )

    def test_apply_to_frontmatter_writes_canonical_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "example.md"
            path.write_text(
                """---
title: Example
tags:
- Artificial Intelligence
- Robotics
search_keywords:
- artificial intelligence
- Robotics
---

Body
""",
                encoding="utf-8",
            )
            lookup = build_lookup(
                {
                    "merges": {
                        "Artificial intelligence": [
                            "Artificial Intelligence",
                            "artificial intelligence",
                        ]
                    }
                }
            )
            changes = apply_to_frontmatter(
                path,
                lookup,
                ("tags", "search_keywords"),
                root=root,
                write=True,
            )
            self.assertEqual(
                changes,
                ["example.md: tags", "example.md: search_keywords"],
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("- Artificial intelligence\n", text)
            self.assertNotIn("Artificial Intelligence", text)

    def test_apply_to_tag_groups_updates_group_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tag_groups.yml"
            path.write_text(
                """groups:
  - label: AI
    tags:
      - Artificial Intelligence
      - Robotics
""",
                encoding="utf-8",
            )
            lookup = build_lookup(
                {
                    "merges": {
                        "Artificial intelligence": ["Artificial Intelligence"],
                    }
                }
            )
            changes = apply_to_tag_groups(path, lookup, write=True)
            self.assertEqual(changes, ["tag_groups.yml: group 'AI'"])
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["groups"][0]["tags"],
                ["Artificial intelligence", "Robotics"],
            )

    def test_suggest_merge_yaml_orders_by_frequency(self):
        yaml_text = suggest_merge_yaml(
            {
                "machine learning": [
                    ("Machine Learning", 6),
                    ("Machine learning", 4),
                    ("machine learning", 2),
                ]
            }
        )
        self.assertIn("Machine Learning", yaml_text)
        self.assertIn("- Machine learning", yaml_text)
        self.assertIn("- machine learning", yaml_text)


if __name__ == "__main__":
    unittest.main()
