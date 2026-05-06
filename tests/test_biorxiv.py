import unittest

from paperutils.fetchers.biorxiv import _biorxiv_item_to_metadata, _latest_biorxiv_item


class BioRxivTests(unittest.TestCase):
    def test_latest_biorxiv_item(self):
        item = _latest_biorxiv_item([
            {"version": "1", "title": "first"},
            {"version": "3", "title": "third"},
            {"version": "2", "title": "second"},
        ])
        self.assertEqual(item["title"], "third")

    def test_biorxiv_item_to_metadata(self):
        result = _biorxiv_item_to_metadata(
            {
                "title": "Cell shape predicts invasion",
                "authors": "Baskaran, J. P.; Weldy, A.; Guarin, J.",
                "doi": "10.1101/2019.12.31.892091",
                "date": "2020-01-01",
                "version": "1",
                "category": "bioengineering",
                "license": "cc_by_nc_nd",
                "type": "new results",
                "jatsxml": "https://www.biorxiv.org/content/early/2020/01/01/2019.12.31.892091.source.xml",
                "abstract": "A test abstract.",
            },
            "biorxiv",
        )

        self.assertEqual(result.title, "Cell shape predicts invasion")
        self.assertEqual(result.authors, ["Baskaran, J. P.", "Weldy, A.", "Guarin, J."])
        self.assertEqual(result.year, "2020")
        self.assertEqual(result.doi, "10.1101/2019.12.31.892091")
        self.assertEqual(result.preprint_server, "biorxiv")
        self.assertEqual(result.preprint_version, "1")
        self.assertIn(
            {"preprint": "https://www.biorxiv.org/content/10.1101/2019.12.31.892091v1.full.pdf"},
            result.full_text_links,
        )


if __name__ == "__main__":
    unittest.main()
