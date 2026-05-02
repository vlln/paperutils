import unittest

from paperutils.models import PaperMetadata
from paperutils.resolver import _merge_metadata


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


if __name__ == "__main__":
    unittest.main()

