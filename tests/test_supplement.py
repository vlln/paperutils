import unittest
from unittest import mock

from paperutils.fetchers.crossref import _crossref_work_to_metadata
from paperutils.fetchers.europepmc import _europepmc_links, _extract_availability_from_xml
from paperutils.fetchers.supplement import enumerate_supplement
from paperutils.http import FetchError
from paperutils.models import PaperMetadata
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

    def test_pmc_xml_data_availability_is_extracted(self):
        text = (
            "Methods. Methods text. "
            "Data availability. "
            "Summary statistics are available from the GWAS Catalog under "
            "accessions GCST90709872 to GCST90711133. "
            "Processed data are available at Zenodo (10.5281/zenodo.14559457). "
            ". Code availability. Code is elsewhere."
        )

        result = _extract_availability_from_xml(text)

        self.assertIsNotNone(result)
        self.assertIn("Data availability", result)
        self.assertIn("GCST90709872", result)
        self.assertIn("10.5281/zenodo.14559457", result)
        self.assertNotIn("Code is elsewhere", result)

    def test_pmc_xml_ignores_irrelevant_content(self):
        text = (
            "Some introduction. "
            "Data availability. Nothing to report. "
            ". Supplementary Materials. Additional file. "
            ". References. [1] Some citation."
        )

        result = _extract_availability_from_xml(text)

        self.assertIsNotNone(result)
        self.assertIn("Nothing to report", result)
        self.assertNotIn("Additional file", result)
        self.assertNotIn("Some citation", result)

    def test_pmc_xml_extracts_with_accessions(self):
        text = (
            "Availability of data and materials. "
            "The sequencing data are available under accession PRJNA123456. "
            ". Supplementary Materials. Additional file 1."
        )

        result = _extract_availability_from_xml(text)

        self.assertIsNotNone(result)
        self.assertIn("PRJNA123456", result)
        self.assertNotIn("Additional file", result)


class SupplementScrapeTests(unittest.TestCase):
    def test_enumerate_no_pmcid_returns_empty(self):
        meta = PaperMetadata(pmcid=None)
        result = enumerate_supplement(meta, timeout=4)
        self.assertEqual(result, [])

    @mock.patch("paperutils.fetchers.supplement.get_text")
    def test_enumerate_from_pmc_html_with_moesm(self, get_text_mock):
        get_text_mock.return_value = """
        <html><body>
        <section id="Sec12">
          <h2>Supplementary Information</h2>
          <section class="sm xbox font-sm" id="MOESM1">
            <a href="/articles/instance/PMC1234567/bin/41598_2024_65538_MOESM1_ESM.pdf"
               data-ga-action="click_feat_suppl">
              Supplementary Figures.
            </a><sup> (412.5KB, pdf)</sup>
          </section>
          <section class="sm xbox font-sm" id="MOESM2">
            <a href="/articles/instance/PMC1234567/bin/41598_2024_65538_MOESM2_ESM.xlsx"
               data-ga-action="click_feat_suppl">
              Supplementary Table 1
            </a><sup> (85.3KB, xlsx)</sup>
          </section>
        </section>
        <section class="associated-data">
          <section class="supplementary-materials">
            <a href="/articles/instance/PMC1234567/bin/41598_2024_65538_MOESM1_ESM.pdf"
               data-ga-action="click_feat_suppl">
              Supplementary Figures.
            </a><sup> (412.5KB, pdf)</sup>
          </section>
        </section>
        </body></html>
        """
        meta = PaperMetadata(pmcid="PMC1234567")
        result = enumerate_supplement(meta, timeout=4)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "41598_2024_65538_MOESM1_ESM.pdf")
        self.assertEqual(
            result[0]["url"],
            "https://pmc.ncbi.nlm.nih.gov/articles/instance/PMC1234567/bin/41598_2024_65538_MOESM1_ESM.pdf",
        )
        self.assertEqual(result[0]["size"], "412.5KB")
        self.assertEqual(result[0]["format"], "pdf")
        self.assertEqual(result[1]["name"], "41598_2024_65538_MOESM2_ESM.xlsx")
        self.assertEqual(result[1]["format"], "xlsx")

    @mock.patch("paperutils.fetchers.supplement.get_text", side_effect=FetchError("connection refused"))
    def test_enumerate_http_error_returns_empty(self, get_text_mock):
        meta = PaperMetadata(pmcid="PMC1234567")
        result = enumerate_supplement(meta, timeout=4)
        self.assertEqual(result, [])

    @mock.patch("paperutils.fetchers.supplement.get_text")
    def test_enumerate_additional_file_pattern(self, get_text_mock):
        get_text_mock.return_value = """
        <html><body>
        <section class="sm xbox font-sm" id="MOESM1">
          <a href="/articles/instance/PMC9999999/bin/Additional_file_1.docx"
             data-ga-action="click_feat_suppl">
            Additional file 1
          </a><sup> (24KB, docx)</sup>
        </section>
        </body></html>
        """
        meta = PaperMetadata(pmcid="PMC9999999")
        result = enumerate_supplement(meta, timeout=4)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Additional_file_1.docx")
        self.assertEqual(result[0]["format"], "docx")

    @mock.patch("paperutils.fetchers.supplement.get_text")
    def test_enumerate_file_without_size_sup(self, get_text_mock):
        get_text_mock.return_value = """
        <html><body>
        <section class="sm xbox font-sm">
          <a href="/articles/instance/PMC1234567/bin/readme.txt"
             data-ga-action="click_feat_suppl">
            README
          </a>
        </section>
        </body></html>
        """
        meta = PaperMetadata(pmcid="PMC1234567")
        result = enumerate_supplement(meta, timeout=4)
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["size"])
        self.assertEqual(result[0]["format"], "txt")


if __name__ == "__main__":
    unittest.main()
