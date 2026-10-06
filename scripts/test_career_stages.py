#!/usr/bin/env python3
"""Checks the career-stage rules in site/_data/career_stages.yml.

The search page groups people by these rules (Students, PhD fellows,
Postdocs/Researchers, Faculty, Others). The page applies them in JavaScript;
this test applies the same patterns in Python to known titles, and prints how
the directory's positions fall, so a new title that lands in the wrong stage
shows up here.
"""
import re
import unittest
from collections import Counter

import yaml

from directory_io import load_entry
from repo_paths import SITE_ROOT

RULES = yaml.safe_load((SITE_ROOT / "_data" / "career_stages.yml").read_text(encoding="utf-8"))


def career_stage(position: str) -> str:
    for stage in RULES["stages"]:
        if any(re.search(p, position or "", re.IGNORECASE) for p in stage["patterns"]):
            return stage["label"]
    return RULES["other"]


class CareerStageTests(unittest.TestCase):
    def test_known_titles(self):
        cases = {
            "Post-doctoral research fellow": "Postdocs/Researchers",
            "Postdoctoral Researcher": "Postdocs/Researchers",
            "Researcher": "Postdocs/Researchers",
            "Research Professor": "Postdocs/Researchers",
            "Research fellow": "PhD fellows",
            "Ph.D Research fellow": "PhD fellows",
            "PHD candidate": "PhD fellows",
            "PhD student": "PhD fellows",
            "Research Assistant, PhD candidate": "PhD fellows",
            "Doctoral Fellow": "PhD fellows",
            "Student": "Students",
            "Master’s Student in Computational Social Science": "Students",
            "Professor": "Faculty",
            "Associate professor": "Faculty",
            "Professor ii": "Faculty",
            "University lecturer": "Faculty",
            "Lektor": "Faculty",
            "Dekan": "Faculty",
            "Pro-rector": "Faculty",
            "University college instructor/student teacher": "Faculty",
            "Senior adviser": "Others",
            "Research Director": "Others",
            "Director": "Others",
            "festival director/CEO": "Others",
            "Rector": "Faculty",
            "": "Others",
        }
        for position, stage in cases.items():
            with self.subTest(position=position):
                self.assertEqual(career_stage(position), stage)

    def test_display_order_lists_every_stage_once(self):
        labels = [s["label"] for s in RULES["stages"]] + [RULES["other"]]
        self.assertEqual(sorted(RULES["display_order"]), sorted(labels))

    def test_every_published_person_gets_a_stage(self):
        counts = Counter()
        for index_md in sorted((SITE_ROOT / "_directory" / "people").glob("*/index.md")):
            if index_md.parent.name.startswith("_"):
                continue
            data, _ = load_entry(index_md)
            if data.get("published") is False:
                continue
            counts[career_stage(str(data.get("position") or ""))] += 1
        labels = [s["label"] for s in RULES["stages"]] + [RULES["other"]]
        self.assertTrue(set(counts) <= set(labels))
        print("\ncareer stages: " + ", ".join(f"{label} {counts[label]}" for label in labels))


if __name__ == "__main__":
    unittest.main()
