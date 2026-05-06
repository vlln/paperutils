import os
import unittest

from paperutils.fetchers import lookup_dataset_resource
from paperutils.fetchers.resources import lookup_zenodo
from paperutils.resolver import explain_accession, find_papers, get_paper


LIVE_TESTS = os.environ.get("PAPERUTILS_LIVE_TESTS") == "1"


@unittest.skipUnless(LIVE_TESTS, "set PAPERUTILS_LIVE_TESTS=1 to run live API smoke tests")
class LiveSmokeTests(unittest.TestCase):
    def test_get_known_doi(self):
        result = get_paper("10.1038/s41586-020-2649-2", depth="fast", timeout=8)
        self.assertEqual(result.identity.doi, "10.1038/s41586-020-2649-2")
        self.assertEqual(result.identity.pmid, "32939066")
        self.assertIn("europepmc", result.sources)

    def test_find_returns_result(self):
        results = find_papers("array programming numpy", limit=1, timeout=8)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(results[0].title)

    def test_explain_geo(self):
        result = explain_accession("GSE100", timeout=8)
        self.assertEqual(result.accession, "GSE100")
        self.assertTrue(result.title or result.status)

    def test_get_arxiv(self):
        result = get_paper("arXiv:1901.01234", depth="fast", timeout=8)
        self.assertTrue(result.identity.arxiv_id.startswith("1901.01234"))
        self.assertIn("arxiv", result.sources)

    def test_get_biorxiv(self):
        result = get_paper("10.1101/2019.12.31.892091", depth="fast", timeout=8)
        self.assertEqual(result.identity.doi, "10.1101/2019.12.31.892091")
        self.assertEqual(result.identity.preprint_server, "biorxiv")
        self.assertIn("biorxiv", result.sources)

    def test_get_medrxiv(self):
        result = get_paper("10.1101/2020.09.09.20191205", depth="fast", timeout=8)
        self.assertEqual(result.identity.doi, "10.1101/2020.09.09.20191205")
        self.assertEqual(result.identity.preprint_server, "medrxiv")
        self.assertIn("medrxiv", result.sources)

    def test_find_cs(self):
        results = find_papers("attention is all you need", domain="cs", limit=1, timeout=8)
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(results[0].arxiv_id)

    def test_lookup_zenodo_live(self):
        result = lookup_zenodo("10.5281/zenodo.13152792", timeout=8)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.get("title"))
        self.assertTrue(result.get("status"))

    def test_lookup_dataset_resource_dispatch(self):
        result = lookup_dataset_resource("10.5281/zenodo.13152792", timeout=8)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.get("title"))

    def test_get_paper_with_zenodo_datasets(self):
        record = get_paper("10.1038/s41588-024-01909-1", depth="full", timeout=10)
        zenodo_datasets = [d for d in record.datasets if d.type == "Zenodo"]
        self.assertGreater(len(zenodo_datasets), 0)
        for ds in zenodo_datasets:
            self.assertTrue(ds.title, f"Zenodo dataset {ds.accession} should have a title")
            self.assertTrue(ds.status, f"Zenodo dataset {ds.accession} should have a status")


if __name__ == "__main__":
    unittest.main()
