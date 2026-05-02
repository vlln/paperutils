import os
import unittest

from paperutils.resolver import lookup, resolve, search


LIVE_TESTS = os.environ.get("PAPERUTILS_LIVE_TESTS") == "1"


@unittest.skipUnless(LIVE_TESTS, "set PAPERUTILS_LIVE_TESTS=1 to run live API smoke tests")
class LiveSmokeTests(unittest.TestCase):
    def test_resolve_known_doi(self):
        result = resolve("10.1038/s41586-020-2649-2", timeout=8)
        self.assertEqual(result.doi, "10.1038/s41586-020-2649-2")
        self.assertEqual(result.pmid, "32939066")
        self.assertIn("europepmc", result.sources)

    def test_search_returns_result(self):
        results = search("array programming numpy", limit=1, timeout=8)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(results[0].title)

    def test_lookup_geo(self):
        result = lookup("GSE100", timeout=8)
        self.assertEqual(result.accession, "GSE100")
        self.assertTrue(result.title or result.status)

    def test_resolve_arxiv(self):
        result = resolve("arXiv:1901.01234", timeout=8)
        self.assertTrue(result.arxiv_id.startswith("1901.01234"))
        self.assertIn("arxiv", result.sources)

    def test_resolve_biorxiv(self):
        result = resolve("10.1101/2019.12.31.892091", timeout=8)
        self.assertEqual(result.doi, "10.1101/2019.12.31.892091")
        self.assertEqual(result.preprint_server, "biorxiv")
        self.assertIn("biorxiv", result.sources)

    def test_resolve_medrxiv(self):
        result = resolve("10.1101/2020.09.09.20191205", timeout=8)
        self.assertEqual(result.doi, "10.1101/2020.09.09.20191205")
        self.assertEqual(result.preprint_server, "medrxiv")
        self.assertIn("medrxiv", result.sources)

    def test_search_cs(self):
        results = search("attention is all you need", domain="cs", limit=1, timeout=8)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(results[0].arxiv_id)


if __name__ == "__main__":
    unittest.main()
