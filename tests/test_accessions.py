import unittest

from paperutils.accessions import classify_accession, extract_accessions


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


if __name__ == "__main__":
    unittest.main()

