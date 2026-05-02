import unittest
from unittest import mock

from paperutils.models import PaperMetadata
from paperutils.resolver import _dataset_records, _enrich_title_resolution_with_canonical_doi, _merge_metadata
from paperutils.models import Accession


class ResolverTests(unittest.TestCase):
    def test_europepmc_data_availability_wins(self):
        target = PaperMetadata(title="Crossref title", abstract="Crossref abstract")
        target.add_source("crossref")
        source = PaperMetadata(
            title="Europe title",
            abstract="Europe abstract",
            data_availability="Data are in GSE123456.",
        )
        source.add_source("europepmc")

        _merge_metadata(target, source)

        self.assertEqual(target.title, "Crossref title")
        self.assertEqual(target.abstract, "Europe abstract")
        self.assertEqual(target.data_availability, "Data are in GSE123456.")
        self.assertEqual(target.sources, ["crossref", "europepmc"])

    def test_higher_confidence_source_replaces_title_candidate(self):
        target = PaperMetadata(
            title="Preprint title",
            journal="bioRxiv",
            doi="10.1101/2025.03.31.25324952",
            confidence=40,
            match_type="title",
        )
        target.add_source("crossref")
        source = PaperMetadata(
            title="Nature title",
            journal="Nature",
            doi="10.1038/s41586-025-10037-7",
            pmid="41234567",
            confidence=100,
            match_type="doi",
        )
        source.add_source("crossref")

        _merge_metadata(target, source)

        self.assertEqual(target.title, "Nature title")
        self.assertEqual(target.journal, "Nature")
        self.assertEqual(target.doi, "10.1038/s41586-025-10037-7")
        self.assertEqual(target.pmid, "41234567")
        self.assertEqual(target.confidence, 100)

    def test_better_title_source_replaces_crossref_title_candidate(self):
        target = PaperMetadata(
            title="Nature title",
            journal="bioRxiv",
            doi="10.1101/2025.03.31.25324952",
            confidence=40,
            match_type="title",
        )
        target.add_source("crossref")
        source = PaperMetadata(
            title="Nature title",
            journal="Nature",
            doi="10.1038/s41586-025-10037-7",
            pmid="41234567",
            pmcid="PMC1234567",
            confidence=70,
            match_type="title",
        )
        source.add_source("europepmc")

        _merge_metadata(target, source)

        self.assertEqual(target.journal, "Nature")
        self.assertEqual(target.doi, "10.1038/s41586-025-10037-7")
        self.assertEqual(target.pmid, "41234567")
        self.assertEqual(target.pmcid, "PMC1234567")

    @mock.patch("paperutils.resolver.CrossrefFetcher")
    def test_canonical_doi_enrichment_adds_publisher_pdf(self, fetcher_class):
        merged = PaperMetadata(
            title="Nature title",
            doi="10.1038/s41586-025-10037-7",
            confidence=40,
            match_type="title",
        )
        merged.add_source("europepmc")
        canonical = PaperMetadata(
            title="Nature title",
            doi="10.1038/s41586-025-10037-7",
            journal="Nature",
            full_text_links=[{"publisher": "https://www.nature.com/articles/s41586-025-10037-7.pdf"}],
            confidence=100,
            match_type="doi",
        )
        canonical.add_source("crossref")
        fetcher_class.return_value.fetch.return_value = canonical

        _enrich_title_resolution_with_canonical_doi(merged, timeout=4)

        self.assertEqual(merged.journal, "Nature")
        self.assertIn(
            {"publisher": "https://www.nature.com/articles/s41586-025-10037-7.pdf"},
            merged.full_text_links,
        )
        fetcher_class.return_value.fetch.assert_called_once()

    def test_dataset_records_do_not_verify_url_resources(self):
        records = _dataset_records(
            [
                Accession("Zenodo", "https://zenodo.org/records/123456", "Processed data"),
                Accession("Figshare", "10.6084/m9.figshare.123456.v1", "Processed data"),
            ],
            verify=True,
            timeout=4,
        )

        self.assertEqual(records[0].type, "Zenodo")
        self.assertEqual(records[0].url, "https://zenodo.org/records/123456")
        self.assertEqual(records[0].download, "https://zenodo.org/records/123456")
        self.assertEqual(records[1].url, "https://doi.org/10.6084/m9.figshare.123456.v1")
        self.assertEqual(records[1].download, "https://doi.org/10.6084/m9.figshare.123456.v1")


if __name__ == "__main__":
    unittest.main()
