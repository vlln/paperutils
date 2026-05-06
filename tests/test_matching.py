import unittest

from paperutils.fetchers.helpers import first_matching_title_candidate
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
            year="2022",
        )
        original = PaperMetadata(
            title="Effect of host genetics on the gut microbiome in 7,738 participants of the Dutch Microbiome Project.",
            doi="10.1038/s41588-021-00992-y",
            year="2022",
        )

        match = first_matching_title_candidate(identifier, [correction, original], "test")

        self.assertEqual(match.doi, "10.1038/s41588-021-00992-y")

    def test_titles_match_short_title_in_citation_like_query(self):
        self.assertTrue(
            titles_match(
                "Pitts N B et al Dental caries Nat Rev Dis Primer 3 17030 2017",
                "Dental caries.",
            )
        )

    def test_first_matching_title_candidate_uses_citation_year(self):
        identifier = Identifier(
            "title",
            "Dental caries Nat Rev Dis Primer 2017 Pitts",
            "Dental caries Nat Rev Dis Primer 2017 Pitts",
        )
        older = PaperMetadata(
            title="Dental caries.",
            doi="10.1016/s0140-6736(00)42916-8",
            year="1944",
        )
        target = PaperMetadata(
            title="Dental caries.",
            doi="10.1038/nrdp.2017.30",
            year="2017",
        )

        match = first_matching_title_candidate(identifier, [older, target], "test")

        self.assertEqual(match.doi, "10.1038/nrdp.2017.30")


if __name__ == "__main__":
    unittest.main()
