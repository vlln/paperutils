import unittest

from paperutils.fetchers import _first_matching_title_candidate
from paperutils.identifiers import Identifier
from paperutils.matching import title_similarity, titles_match
from paperutils.models import PaperMetadata


class MatchingTests(unittest.TestCase):
    def test_titles_match_normalized_variants(self):
        self.assertTrue(
            titles_match(
                "A Spatially Resolved Brain Atlas of Gene Expression in Alzheimer's Disease",
                "Spatially resolved brain atlas of gene expression in Alzheimer's disease.",
            )
        )

    def test_titles_reject_unrelated_candidate(self):
        score = title_similarity(
            "Spatially resolved brain atlas of gene expression in Alzheimer's disease",
            "Single cell analysis of immune responses in viral infection",
        )
        self.assertLess(score, 0.5)
        self.assertFalse(
            titles_match(
                "Spatially resolved brain atlas of gene expression in Alzheimer's disease",
                "Single cell analysis of immune responses in viral infection",
            )
        )

    def test_titles_reject_short_title_inside_longer_candidate(self):
        score = title_similarity(
            "The human oral microbiome",
            "The exposome and the human oral microbiome through the one health lens",
        )

        self.assertLess(score, 0.82)
        self.assertFalse(
            titles_match(
                "The human oral microbiome",
                "The exposome and the human oral microbiome through the one health lens",
            )
        )

    def test_titles_reject_unrequested_author_correction(self):
        self.assertFalse(
            titles_match(
                "Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project",
                "Author Correction: Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project.",
            )
        )

    def test_first_matching_title_candidate_skips_author_correction(self):
        identifier = Identifier(
            "title",
            "Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project",
            "Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project",
        )
        correction = PaperMetadata(
            title="Author Correction: Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project.",
            doi="10.1038/s41588-022-01164-2",
        )
        original = PaperMetadata(
            title="Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project.",
            doi="10.1038/s41588-021-00992-y",
        )

        match = _first_matching_title_candidate(identifier, [correction, original], "test")

        self.assertEqual(match.doi, "10.1038/s41588-021-00992-y")


if __name__ == "__main__":
    unittest.main()
