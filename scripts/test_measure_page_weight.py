#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_page_weight import weigh


class Tests(unittest.TestCase):
    def test_sums_html_and_local_assets_once(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d)
            (site / "assets" / "css").mkdir(parents=True)
            (site / "assets" / "css" / "a.css").write_text("body{}" * 100)
            (site / "img.png").write_bytes(b"\x89PNG" + b"0" * 199996)
            (site / "index.html").write_text('<link href="/assets/css/a.css"><img src="/img.png"><img src="/img.png"><script src="https://cdn.example/x.js"></script>')
            r = weigh(site, "/")
            self.assertEqual(r["requests"], 3)
            self.assertEqual(r["by_kind"]["images"], 200000)
            self.assertLess(r["by_kind"]["styles"], 600)   # gzip-compressed text
            self.assertGreater(r["g_co2_first_visit"], 0)


if __name__ == "__main__":
    unittest.main()
