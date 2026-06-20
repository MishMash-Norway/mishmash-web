#!/usr/bin/env python3
import unittest

from nva_result_types import exclude_from_person_profile, result_group_type


class ExcludePersonProfileResultsTests(unittest.TestCase):
    def test_excludes_regular_lectures(self):
        self.assertTrue(exclude_from_person_profile("Lecture"))
        self.assertTrue(exclude_from_person_profile("OtherPresentation"))
        self.assertEqual(result_group_type("ConferenceLecture"), "Conference")
        self.assertFalse(exclude_from_person_profile("ConferenceLecture"))

    def test_excludes_media_appearances(self):
        self.assertTrue(exclude_from_person_profile("MediaInterview"))
        self.assertTrue(exclude_from_person_profile("MediaParticipationInRadioOrTv"))
        self.assertTrue(exclude_from_person_profile(group_type="Media"))

    def test_keeps_publications(self):
        self.assertFalse(exclude_from_person_profile("AcademicArticle"))
        self.assertFalse(exclude_from_person_profile("JournalArticle"))
        self.assertFalse(exclude_from_person_profile("PopularScienceArticle"))


if __name__ == "__main__":
    unittest.main()
