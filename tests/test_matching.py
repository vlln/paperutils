import unittest

from paperutils.matching import title_similarity, titles_match


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


if __name__ == "__main__":
    unittest.main()
