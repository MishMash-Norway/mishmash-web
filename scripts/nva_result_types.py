"""Human-readable labels for NVA publication instance types (CategoryEnum).

The NVA search API returns machine-readable codes in
``reference.publicationInstance.type``. The OpenAPI schema defines the full
``CategoryEnum`` list but does not attach descriptions to individual values.
Cristin user documentation describes the underlying categories in plain language;
these labels follow that terminology where it helps readability.
"""

from __future__ import annotations

import re

MEDIA_RESULT_TYPES = {
    "MediaBlogPost",
    "MediaFeatureArticle",
    "MediaInterview",
    "MediaParticipationInRadioOrTv",
    "MediaReaderOpinion",
}
MEDIA_GROUP_LABEL = "Media"
PERSON_PROFILE_EXCLUDED_INSTANCE_TYPES = MEDIA_RESULT_TYPES | {
    "Lecture",
    "OtherPresentation",
}
PERSON_PROFILE_EXCLUDED_GROUP_TYPES = {
    MEDIA_GROUP_LABEL,
    "Lecture",
}

# Curated labels for types we display or expect to encounter. Unknown types fall
# back to camelCase splitting via nva_result_type_label().
NVA_TYPE_LABELS: dict[str, str] = {
    "AcademicArticle": "Journal article",
    "AcademicChapter": "Book chapter",
    "AcademicLiteratureReview": "Literature review",
    "AcademicMonograph": "Monograph",
    "Architecture": "Architecture",
    "ArtisticDesign": "Design",
    "BookAbstracts": "Book of abstracts",
    "BookAnthology": "Book anthology",
    "BookMonograph": "Book",
    "CaseReport": "Case report",
    "ChapterArticle": "Chapter",
    "ChapterConferenceAbstract": "Conference abstract",
    "ChapterInReport": "Chapter in report",
    "ConferenceAbstract": "Conference abstract",
    "ConferenceLecture": "Conference lecture",
    "ConferencePoster": "Conference poster",
    "ConferenceReport": "Conference report",
    "DataManagementPlan": "Data management plan",
    "DataSet": "Dataset",
    "DegreeBachelor": "Bachelor's thesis",
    "DegreeLicentiate": "Licentiate thesis",
    "DegreeMaster": "Master's thesis",
    "DegreePhd": "PhD thesis",
    "Encyclopedia": "Encyclopedia",
    "EncyclopediaChapter": "Encyclopedia chapter",
    "ExhibitionCatalog": "Exhibition catalog",
    "ExhibitionCatalogChapter": "Exhibition catalog chapter",
    "ExhibitionProduction": "Exhibition",
    "FeatureArticle": "Feature article",
    "Introduction": "Introduction",
    "JournalArticle": "Journal article",
    "JournalCorrigendum": "Corrigendum",
    "JournalInterview": "Journal interview",
    "JournalIssue": "Journal issue",
    "JournalLeader": "Editorial",
    "JournalLetter": "Letter to the editor",
    "JournalReview": "Book review",
    "Lecture": "Lecture",
    "LiteraryArts": "Literary arts",
    "MediaBlogPost": "Blog post",
    "MediaFeatureArticle": "Feature article",
    "MediaInterview": "Interview",
    "MediaParticipationInRadioOrTv": "Radio or TV",
    "MediaReaderOpinion": "Reader opinion",
    "MovingPicture": "Film or video",
    "MusicPerformance": "Music performance",
    "NonFictionChapter": "Non-fiction chapter",
    "NonFictionMonograph": "Non-fiction book",
    "OtherPresentation": "Presentation",
    "OtherStudentWork": "Student work",
    "PerformingArts": "Performing arts",
    "PopularScienceArticle": "Popular science article",
    "PopularScienceChapter": "Popular science chapter",
    "PopularScienceMonograph": "Popular science book",
    "ProfessionalArticle": "Professional article",
    "ReportBasic": "Report",
    "ReportBookOfAbstract": "Book of abstracts",
    "ReportPolicy": "Policy report",
    "ReportResearch": "Research report",
    "ReportWorkingPaper": "Working paper",
    "StudyProtocol": "Study protocol",
    "Textbook": "Textbook",
    "TextbookChapter": "Textbook chapter",
    "VisualArts": "Visual arts",
}

# Filter chips and section headings on /results/ use broader groups for some types.
GROUP_TYPE_LABELS: dict[str, str] = {
    "AcademicArticle": "Journal article",
    "JournalArticle": "Journal article",
    "AcademicChapter": "Book chapter",
    "ChapterInReport": "Book chapter",
    "ConferenceAbstract": "Conference",
    "ConferenceLecture": "Conference",
    "ConferencePoster": "Conference",
    "ConferenceReport": "Conference",
    "Lecture": "Lecture",
    "OtherPresentation": "Lecture",
}


def nva_publication_instance_type(reference: dict) -> str:
    reference = reference or {}
    instance = reference.get("publicationInstance") or {}
    return (instance.get("type") or "").strip()


def nva_result_type_label(instance_type: str) -> str:
    instance_type = (instance_type or "").strip()
    if not instance_type:
        return "Publication"
    if instance_type in NVA_TYPE_LABELS:
        return NVA_TYPE_LABELS[instance_type]
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", instance_type).strip()
    if not spaced:
        return instance_type
    return spaced[0].upper() + spaced[1:].lower()


def result_group_type(instance_type: str) -> str:
    instance_type = (instance_type or "").strip()
    if instance_type in MEDIA_RESULT_TYPES or (
        instance_type.startswith("Media") and instance_type != MEDIA_GROUP_LABEL
    ):
        return MEDIA_GROUP_LABEL
    if instance_type in GROUP_TYPE_LABELS:
        return GROUP_TYPE_LABELS[instance_type]
    return nva_result_type_label(instance_type)


def exclude_from_person_profile(
    instance_type: str = "",
    *,
    group_type: str = "",
    source: str = "",
) -> bool:
    instance_type = (instance_type or "").strip()
    if instance_type:
        if instance_type in PERSON_PROFILE_EXCLUDED_INSTANCE_TYPES:
            return True
        if instance_type.startswith("Media"):
            return True

    group_type = (group_type or "").strip()
    if group_type in PERSON_PROFILE_EXCLUDED_GROUP_TYPES:
        return True

    source_label = (source or "").strip().lower()
    if source_label:
        excluded_sources = {
            nva_result_type_label(item).lower()
            for item in PERSON_PROFILE_EXCLUDED_INSTANCE_TYPES
        }
        excluded_sources.update(label.lower() for label in PERSON_PROFILE_EXCLUDED_GROUP_TYPES)
        if source_label in excluded_sources:
            return True

    return False


def nva_publication_source(reference: dict) -> str:
    """Return a display label for a publication reference (legacy helper name)."""
    return nva_result_type_label(nva_publication_instance_type(reference))
