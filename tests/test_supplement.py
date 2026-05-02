import unittest

from paperutils.fetchers import _crossref_work_to_metadata, _europepmc_links, _extract_availability_from_html
from paperutils.resolver import _supplement_from_links


class SupplementTests(unittest.TestCase):
    def test_crossref_supplement_links_are_classified(self):
        result = _crossref_work_to_metadata(
            {
                "title": ["Example"],
                "DOI": "10.1038/example",
                "link": [
                    {
                        "URL": "https://www.nature.com/articles/example.pdf",
                        "content-type": "application/pdf",
                    },
                    {
                        "URL": "https://www.nature.com/articles/example-supplementary.pdf",
                        "content-type": "application/pdf",
                        "intended-application": "supplementary-material",
                    },
                ],
                "relation": {
                    "is-supplemented-by": [
                        {"id-type": "doi", "id": "10.1038/example-s1"},
                    ]
                },
            },
            "crossref",
        )

        self.assertIn({"publisher": "https://www.nature.com/articles/example.pdf"}, result.full_text_links)
        self.assertIn(
            {"supplement": "https://www.nature.com/articles/example-supplementary.pdf"},
            result.full_text_links,
        )
        self.assertIn({"supplement": "https://doi.org/10.1038/example-s1"}, result.full_text_links)

    def test_europepmc_supplement_links_are_classified(self):
        links = _europepmc_links(
            {
                "fullTextUrlList": {
                    "fullTextUrl": [
                        {
                            "url": "https://europepmc.org/articles/example/supplementary.pdf",
                            "site": "Europe PMC",
                            "documentStyle": "supplementary material",
                        }
                    ]
                }
            }
        )

        self.assertEqual(links, [{"supplement": "https://europepmc.org/articles/example/supplementary.pdf"}])

    def test_supplement_summary_uses_structured_files(self):
        result = _supplement_from_links(
            [
                {"publisher": "https://www.nature.com/articles/example.pdf"},
                {"supplement": "https://www.nature.com/articles/example-supplementary.pdf"},
                {"jatsxml": "https://www.biorxiv.org/content/example.source.xml"},
                {"supplement": "https://www.nature.com/articles/example-supplementary.pdf"},
            ]
        )

        self.assertEqual(result["pdf"], "https://www.nature.com/articles/example.pdf")
        self.assertEqual(
            result["files"],
            [
                {"type": "supplement", "url": "https://www.nature.com/articles/example-supplementary.pdf"},
                {"type": "jatsxml", "url": "https://www.biorxiv.org/content/example.source.xml"},
            ],
        )

    def test_pmc_html_data_availability_is_extracted(self):
        html = """
        <html><body>
          <h2>Methods</h2><p>Methods text.</p>
          <h2>Data availability</h2>
          <p>Summary statistics are available from the GWAS Catalog under
          accessions GCST90709872 to GCST90711133.</p>
          <p>Processed data are available at Zenodo (10.5281/zenodo.14559457).</p>
          <h2>Code availability</h2><p>Code is elsewhere.</p>
        </body></html>
        """

        text = _extract_availability_from_html(html)

        self.assertIn("Data availability", text)
        self.assertIn("GCST90709872", text)
        self.assertIn("10.5281/zenodo.14559457", text)
        self.assertNotIn("Code is elsewhere", text)


if __name__ == "__main__":
    unittest.main()
