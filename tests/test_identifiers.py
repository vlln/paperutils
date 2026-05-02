import unittest

from paperutils.identifiers import infer_domain, parse_identifier


class IdentifierTests(unittest.TestCase):
    def test_parse_doi(self):
        identifier = parse_identifier("https://doi.org/10.1038/s41586-023-05564-0")
        self.assertEqual(identifier.kind, "doi")
        self.assertEqual(identifier.value, "10.1038/s41586-023-05564-0")

    def test_parse_pubmed_url(self):
        identifier = parse_identifier("https://pubmed.ncbi.nlm.nih.gov/36653456/")
        self.assertEqual(identifier.kind, "pmid")
        self.assertEqual(identifier.value, "36653456")

    def test_parse_pmcid(self):
        identifier = parse_identifier("PMCID:PMC9876543")
        self.assertEqual(identifier.kind, "pmcid")
        self.assertEqual(identifier.value, "PMC9876543")

    def test_arxiv_domain(self):
        identifier = parse_identifier("arXiv:1901.01234")
        self.assertEqual(identifier.kind, "arxiv")
        self.assertEqual(infer_domain(identifier), "cs")

    def test_title_fallback(self):
        identifier = parse_identifier("A spatially resolved brain atlas")
        self.assertEqual(identifier.kind, "title")


if __name__ == "__main__":
    unittest.main()

