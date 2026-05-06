"""Offline tests for dataset resource lookup helpers."""

import unittest

from paperutils.fetchers.helpers import date_prefix, join_creators
from paperutils.fetchers.resources import (
    _extract_dryad_doi,
    _extract_figshare_id,
    _extract_osf_guid,
    _extract_zenodo_id,
    _format_file_size,
    lookup_dataset_resource,
    lookup_dryad,
    lookup_figshare,
    lookup_osf,
    lookup_zenodo,
)


class ResourceIdExtractionTests(unittest.TestCase):
    def test_extract_zenodo_id_from_doi(self):
        self.assertEqual(_extract_zenodo_id("10.5281/zenodo.13152792"), "13152792")

    def test_extract_zenodo_id_from_url(self):
        self.assertEqual(
            _extract_zenodo_id("https://zenodo.org/records/4651413"),
            "4651413",
        )

    def test_extract_zenodo_id_from_api_url(self):
        self.assertEqual(
            _extract_zenodo_id("https://zenodo.org/api/records/12345678"),
            "12345678",
        )

    def test_extract_zenodo_id_no_match(self):
        self.assertIsNone(_extract_zenodo_id("10.1038/s41586-020-2649-2"))

    def test_extract_figshare_id_from_doi(self):
        self.assertEqual(
            _extract_figshare_id("10.6084/m9.figshare.12345678.v1"),
            "12345678",
        )

    def test_extract_figshare_id_from_url(self):
        self.assertEqual(
            _extract_figshare_id("https://figshare.com/articles/dataset/Some_title/12345678"),
            "12345678",
        )

    def test_extract_figshare_id_no_match(self):
        self.assertIsNone(_extract_figshare_id("10.1038/s41586-020-2649-2"))

    def test_extract_dryad_doi_from_doi(self):
        self.assertEqual(
            _extract_dryad_doi("10.5061/dryad.7rh4625"),
            "10.5061/dryad.7rh4625",
        )

    def test_extract_dryad_doi_with_trailing_punctuation(self):
        self.assertEqual(
            _extract_dryad_doi("10.5061/dryad.abc123."),
            "10.5061/dryad.abc123",
        )

    def test_extract_dryad_doi_no_match(self):
        self.assertIsNone(_extract_dryad_doi("10.5281/zenodo.12345678"))

    def test_extract_osf_guid_from_doi(self):
        self.assertEqual(
            _extract_osf_guid("10.17605/osf.io/abcde"),
            "abcde",
        )

    def test_extract_osf_guid_from_url(self):
        self.assertEqual(
            _extract_osf_guid("https://osf.io/xyz12/"),
            "xyz12",
        )

    def test_extract_osf_guid_no_match(self):
        self.assertIsNone(_extract_osf_guid("10.1038/s41586-020-2649-2"))


class FormatHelpersTests(unittest.TestCase):
    def test_format_file_size_bytes(self):
        self.assertEqual(_format_file_size(500), "500 B")

    def test_format_file_size_kb(self):
        self.assertEqual(_format_file_size(2000), "2 KB")

    def test_format_file_size_mb(self):
        self.assertEqual(_format_file_size(5_000_000), "5 MB")

    def test_format_file_size_gb(self):
        self.assertEqual(_format_file_size(2_500_000_000), "2.5 GB")

    def test_date_prefix_iso_datetime(self):
        self.assertEqual(date_prefix("2023-01-15T12:30:00Z"), "2023-01-15")

    def test_date_prefix_short_date(self):
        self.assertEqual(date_prefix("2023-01-15"), "2023-01-15")

    def test_date_prefix_none(self):
        self.assertIsNone(date_prefix(None))

    def test_date_prefix_too_short(self):
        self.assertIsNone(date_prefix("2023"))

    def test_join_creators(self):
        creators = [
            {"name": "Smith J", "affiliation": "UCL"},
            {"name": "Doe K", "affiliation": "MIT"},
        ]
        self.assertEqual(join_creators(creators), "Smith J, Doe K")

    def test_join_creators_empty(self):
        self.assertIsNone(join_creators([]))

    def test_join_creators_custom_key(self):
        creators = [{"full_name": "Smith J"}, {"full_name": "Doe K"}]
        self.assertEqual(join_creators(creators, key="full_name"), "Smith J, Doe K")


class ZenodoLookupTests(unittest.TestCase):
    def test_parses_valid_response(self):
        data = {
            "title": "Processed scRNA-seq data for AD brain atlas",
            "metadata": {
                "title": "Processed scRNA-seq data for AD brain atlas",
                "publication_date": "2023-05-12",
                "description": "Contains normalized counts, metadata, and clustering results.",
                "creators": [
                    {"name": "Smith J", "affiliation": "UCL"},
                    {"name": "Doe K"},
                ],
                "access_right": "open",
            },
            "status": "published",
            "files": [
                {
                    "key": "counts.h5ad",
                    "size": 234_000_000,
                    "links": {"self": "https://zenodo.org/records/123/files/counts.h5ad"},
                },
                {
                    "key": "metadata.csv",
                    "size": 120_000,
                    "links": {"self": "https://zenodo.org/records/123/files/metadata.csv"},
                },
            ],
        }

        import json
        import urllib.request
        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.get_json", return_value=data):
            result = lookup_zenodo("10.5281/zenodo.12345678", timeout=4)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["title"], "Processed scRNA-seq data for AD brain atlas")
        self.assertEqual(result["description"], "Contains normalized counts, metadata, and clustering results.")
        self.assertEqual(result["creators"], "Smith J, Doe K")
        self.assertEqual(result["published"], "2023-05-12")
        self.assertEqual(result["status"], "published")
        self.assertEqual(len(result["files"]), 2)
        self.assertEqual(result["files"][0]["name"], "counts.h5ad")
        self.assertEqual(result["files"][0]["size"], "234 MB")
        self.assertEqual(
            result["files"][0]["download"],
            "https://zenodo.org/records/123/files/counts.h5ad",
        )
        self.assertEqual(result["files"][1]["name"], "metadata.csv")
        self.assertEqual(result["files"][1]["size"], "120 KB")


class FigshareLookupTests(unittest.TestCase):
    def test_parses_valid_response(self):
        data = {
            "title": "Test dataset",
            "description": "<p>Dataset description here.</p>",
            "published_date": "2022-06-15T10:00:00Z",
            "is_public": True,
            "authors": [
                {"full_name": "Jones A", "orcid_id": "0000-0001-2345-6789"},
                {"full_name": "Brown B"},
            ],
            "files": [
                {
                    "name": "data.csv",
                    "size": 5_200_000,
                    "download_url": "https://api.figshare.com/v2/articles/999/files/data.csv",
                },
            ],
        }

        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.get_json", return_value=data):
            result = lookup_figshare("10.6084/m9.figshare.12345678.v1", timeout=4)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["title"], "Test dataset")
        self.assertEqual(result["creators"], "Jones A, Brown B")
        self.assertEqual(result["published"], "2022-06-15")
        self.assertEqual(result["status"], "public")
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["name"], "data.csv")
        self.assertEqual(result["files"][0]["size"], "5 MB")


class DryadLookupTests(unittest.TestCase):
    def test_parses_valid_response(self):
        data = {
            "title": "Data from: A study of coral reefs",
            "abstract": "This dataset contains measurements from 50 sites.",
            "publicationDate": "2021-03-20",
            "visibility": "public",
            "curationStatus": "Published",
            "authors": [
                {"firstName": "Alice", "lastName": "Wang", "affiliation": "UQ"},
                {"firstName": "Bob", "lastName": "Li"},
            ],
        }

        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.get_json", return_value=data):
            result = lookup_dryad("10.5061/dryad.abc123", timeout=4)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["title"], "Data from: A study of coral reefs")
        self.assertEqual(result["description"], "This dataset contains measurements from 50 sites.")
        self.assertEqual(result["creators"], "Alice Wang, Bob Li")
        self.assertEqual(result["published"], "2021-03-20")
        self.assertEqual(result["status"], "public")


class OSFLookupTests(unittest.TestCase):
    def test_parses_valid_response(self):
        data = {
            "data": {
                "attributes": {
                    "title": "Preregistration: Effect of sleep on memory",
                    "description": "This preregistration outlines the planned analysis.",
                    "date_created": "2024-01-10T08:30:00Z",
                    "date_modified": "2024-02-15T14:00:00Z",
                    "public": True,
                    "category": "project",
                }
            }
        }

        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.get_json", return_value=data):
            result = lookup_osf("10.17605/osf.io/abcde", timeout=4)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["title"], "Preregistration: Effect of sleep on memory")
        self.assertEqual(result["description"], "This preregistration outlines the planned analysis.")
        self.assertEqual(result["published"], "2024-01-10")
        self.assertEqual(result["status"], "public")
        self.assertIsNone(result["creators"])
        self.assertIsNone(result["files"])


class DispatcherTests(unittest.TestCase):
    def test_dispatches_to_zenodo(self):
        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.lookup_zenodo", return_value={"title": "Z"}) as m:
            result = lookup_dataset_resource("10.5281/zenodo.12345678", timeout=4)
            m.assert_called_once()
        self.assertEqual(result, {"title": "Z"})

    def test_dispatches_to_figshare(self):
        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.lookup_figshare", return_value={"title": "F"}) as m:
            result = lookup_dataset_resource("10.6084/m9.figshare.123.v1", timeout=4)
            m.assert_called_once()
        self.assertEqual(result, {"title": "F"})

    def test_dispatches_to_dryad(self):
        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.lookup_dryad", return_value={"title": "D"}) as m:
            result = lookup_dataset_resource("10.5061/dryad.abc", timeout=4)
            m.assert_called_once()
        self.assertEqual(result, {"title": "D"})

    def test_dispatches_to_osf(self):
        from unittest import mock

        with mock.patch("paperutils.fetchers.resources.lookup_osf", return_value={"title": "O"}) as m:
            result = lookup_dataset_resource("10.17605/osf.io/abcde", timeout=4)
            m.assert_called_once()
        self.assertEqual(result, {"title": "O"})

    def test_returns_none_for_unknown(self):
        self.assertIsNone(lookup_dataset_resource("10.1038/s41586-020-2649-2", timeout=4))


if __name__ == "__main__":
    unittest.main()
