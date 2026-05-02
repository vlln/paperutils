import unittest

from paperutils.accessions import (
    classify_accession,
    extract_accessions,
    extract_code_repos,
    extract_dataset_resources,
)


class AccessionTests(unittest.TestCase):
    def test_extract_accessions(self):
        text = (
            "Raw data are available under GEO accession GSE123456. "
            "Sequencing reads are in PRJNA765432 and SRP111222."
        )
        found = extract_accessions(text)
        self.assertEqual([item.accession for item in found], ["GSE123456", "SRP111222", "PRJNA765432"])

    def test_classify_accession(self):
        self.assertEqual(classify_accession("GSE123456"), "GEO")
        self.assertEqual(classify_accession("PRJEB54321"), "ENA")
        self.assertEqual(classify_accession("GCA_000001405.29"), "Assembly")

    def test_extract_code_repos(self):
        text = (
            "Code is available at https://github.com/example-lab/paper-code/tree/main "
            "and mirrored at https://github.com/example-lab/paper-code."
        )
        self.assertEqual(
            extract_code_repos(text),
            [{"url": "https://github.com/example-lab/paper-code", "source": "data_availability"}],
        )

    def test_extract_dataset_resources(self):
        text = (
            "Processed data are at https://zenodo.org/records/123456 and "
            "Figshare DOI 10.6084/m9.figshare.123456.v1. "
            "Dryad data: https://datadryad.org/dataset/doi:10.5061/dryad.ab12cd3."
        )
        found = extract_dataset_resources(text)
        self.assertEqual(
            [(item.type, item.accession) for item in found],
            [
                ("Zenodo", "https://zenodo.org/records/123456"),
                ("Dryad", "https://datadryad.org/dataset/doi:10.5061/dryad.ab12cd3"),
                ("Figshare", "10.6084/m9.figshare.123456.v1"),
                ("Dryad", "10.5061/dryad.ab12cd3"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
