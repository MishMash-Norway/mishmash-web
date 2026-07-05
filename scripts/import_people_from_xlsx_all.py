#!/usr/bin/env python3
"""Compatibility wrapper for the all-rows XLSX people import."""

import sys

from import_people_from_xlsx import main as import_people_main


if __name__ == "__main__":
    raise SystemExit(import_people_main(sys.argv[1:]))
