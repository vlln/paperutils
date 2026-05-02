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
            "Sequencing reads are in PRJNA765432 and SRP111222. "
            "CNGB data are under CNP0003685."
        )
        found = extract_accessions(text)
        self.assertEqual(
            [item.accession for item in found],
            ["GSE123456", "SRP111222", "PRJNA765432", "CNP0003685"],
        )

    def test_extract_ena_submission_and_study_accessions(self):
        text = (
            "Published metagenomics datasets analyzed here are available from ENA: "
            "accession number ERA000116 (Qin et al, 2010) and ERP003612 "
            "(Le Chatelier et al, 2013). The sample accession is ERS581126."
        )
        found = extract_accessions(text)
        self.assertEqual(
            [(item.type, item.accession) for item in found],
            [("ENA", "ERA000116"), ("ENA", "ERP003612"), ("ENA", "ERS581126")],
        )

    def test_classify_accession(self):
        self.assertEqual(classify_accession("GSE123456"), "GEO")
        self.assertEqual(classify_accession("ERA000116"), "ENA")
        self.assertEqual(classify_accession("PRJEB54321"), "ENA")
        self.assertEqual(classify_accession("GCA_000001405.29"), "Assembly")
        self.assertEqual(classify_accession("CNP0003685"), "CNGB")

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
            "Dryad data: https://datadryad.org/dataset/doi:10.5061/dryad.ab12cd3. "
            "CNGB data are at https://db.cngb.org/search/project/CNP0001664."
        )
        found = extract_dataset_resources(text)
        self.assertEqual(
            [(item.type, item.accession) for item in found],
            [
                ("Zenodo", "https://zenodo.org/records/123456"),
                ("Dryad", "https://datadryad.org/dataset/doi:10.5061/dryad.ab12cd3"),
                ("CNGB", "https://db.cngb.org/search/project/CNP0001664"),
                ("Figshare", "10.6084/m9.figshare.123456.v1"),
                ("Dryad", "10.5061/dryad.ab12cd3"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
