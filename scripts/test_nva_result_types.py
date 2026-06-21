#!/usr/bin/env python3
import unittest

from nva_result_types import exclude_from_person_profile, result_group_type


class ExcludePersonProfileResultsTests(unittest.TestCase):
    def test_excludes_regular_lectures(self):
        self.assertTrue(exclude_from_person_profile("Lecture"))
        self.assertTrue(exclude_from_person_profile("ConferenceLecture"))
        self.assertTrue(exclude_from_person_profile("OtherPresentation"))
        self.assertEqual(result_group_type("ConferenceLecture"), "Conference")
        self.assertTrue(exclude_from_person_profile(source="Conference lecture"))

    def test_excludes_media_appearances(self):
        self.assertTrue(exclude_from_person_profile("MediaInterview"))
        self.assertTrue(exclude_from_person_profile("MediaParticipationInRadioOrTv"))
        self.assertTrue(exclude_from_person_profile(group_type="Media"))

    def test_keeps_publications(self):
        self.assertFalse(exclude_from_person_profile("AcademicArticle"))
        self.assertFalse(exclude_from_person_profile("JournalArticle"))
        self.assertFalse(exclude_from_person_profile("PopularScienceArticle"))

    def test_excludes_letters_to_the_editor(self):
        self.assertTrue(exclude_from_person_profile("JournalLetter"))
        self.assertTrue(exclude_from_person_profile(group_type="Letter to the editor"))
        self.assertTrue(exclude_from_person_profile(source="Letter to the editor"))


if __name__ == "__main__":
    unittest.main()
