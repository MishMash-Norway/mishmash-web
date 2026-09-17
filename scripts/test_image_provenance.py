#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from image_provenance import add_svg_metadata, svg_source_type, xmp_block

SVG = '<svg width="10" height="10" xmlns="http://www.w3.org/2000/svg"><circle r="4"/></svg>'


class Tests(unittest.TestCase):
    def test_insert_and_read(self):
        out = add_svg_metadata(SVG, xmp_block("algorithmicMedia", "test"))
        self.assertTrue(out.startswith('<svg width="10"'))
        self.assertIn("<metadata>", out)
        self.assertEqual(svg_source_type(out), "algorithmicMedia")
        self.assertIn("<circle", out)

    def test_replace_existing(self):
        once = add_svg_metadata(SVG, xmp_block("algorithmicMedia", "a"))
        twice = add_svg_metadata(once, xmp_block("trainedAlgorithmicMedia", "b"))
        self.assertEqual(twice.count("<metadata>"), 1)
        self.assertEqual(svg_source_type(twice), "trainedAlgorithmicMedia")

    def test_unknown_type_rejected(self):
        with self.assertRaises(AssertionError):
            xmp_block("magic", "x")


if __name__ == "__main__":
    unittest.main()
