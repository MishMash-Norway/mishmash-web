#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tag_merge import (
    apply_all,
    apply_to_frontmatter,
    apply_to_tag_groups,
    build_lookup,
    merge_tag_list,
    suggest_merge_yaml,
    title_case_tag,
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
        self.assertEqual(lookup["Artificial Intelligence"], "Artificial Intelligence")
        self.assertEqual(lookup["Artificial intelligence"], "Artificial Intelligence")
        self.assertEqual(lookup["AI"], "Artificial Intelligence")
        self.assertEqual(lookup["Digital libary"], "Digital Library")

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
- AI
- Robotics
search_keywords:
- AI
- Robotics
---

Body
""",
                encoding="utf-8",
            )
            lookup = build_lookup(
                {
                    "merges": {
                        "Artificial Intelligence": ["AI"]
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
            self.assertIn("- Artificial Intelligence\n", text)
            self.assertNotIn("Artificial intelligence", text)

    def test_apply_to_tag_groups_updates_group_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tag_groups.yml"
            path.write_text(
                """groups:
  - label: AI
    tags:
      - AI
      - Robotics
""",
                encoding="utf-8",
            )
            lookup = build_lookup(
                {
                    "merges": {
                        "Artificial Intelligence": ["AI"],
                    }
                }
            )
            changes = apply_to_tag_groups(path, lookup, write=True)
            self.assertEqual(changes, ["tag_groups.yml: group 'AI'"])
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["groups"][0]["tags"],
                ["Artificial Intelligence", "Robotics"],
            )

    def test_apply_all_without_map_capitalizes_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "page.md"
            page.write_text(
                """---
title: Example
tags:
- machine learning
- art and design
search_keywords:
- human computer interaction
roles:
- work package leader
---

Body
""",
                encoding="utf-8",
            )
            tag_groups = root / "tag_groups.yml"
            tag_groups.write_text(
                """groups:
  - label: Example
    tags:
      - art and design
""",
                encoding="utf-8",
            )

            file_changes, group_changes = apply_all(
                root=root,
                map_path=None,
                tag_groups_path=tag_groups,
                write=True,
            )

            self.assertEqual(
                file_changes,
                ["page.md: tags", "page.md: search_keywords", "page.md: roles"],
            )
            self.assertEqual(group_changes, ["tag_groups.yml: group 'Example'"])

            text = page.read_text(encoding="utf-8")
            self.assertIn("- Machine Learning\n", text)
            self.assertIn("- Art and Design\n", text)
            self.assertIn("- Human Computer Interaction\n", text)
            self.assertIn("- Work Package Leader\n", text)

    def test_title_case_tag_capitalizes_words_and_preserves_connectors(self):
        self.assertEqual(
            title_case_tag("technology, innovation and culture"),
            "Technology, Innovation and Culture",
        )

    def test_title_case_tag_preserves_acronyms_and_brand_casing(self):
        self.assertEqual(
            title_case_tag("AI and GitHub in WP1"),
            "AI and GitHub in WP1",
        )

    def test_title_case_tag_capitalizes_words_after_separators(self):
        self.assertEqual(
            title_case_tag("sound/music in new media"),
            "Sound/Music in New Media",
        )

    def test_title_case_tag_capitalizes_first_and_last_connector_words(self):
        self.assertEqual(
            title_case_tag("the sound of music"),
            "The Sound of Music",
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
