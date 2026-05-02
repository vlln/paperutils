import unittest

from paperutils.fetchers import _arxiv_entries, _arxiv_entry_to_metadata, _arxiv_entry_to_search


ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/1901.01234v2</id>
    <updated>2020-01-02T00:00:00Z</updated>
    <published>2019-01-04T00:00:00Z</published>
    <title>  Example   arXiv Paper  </title>
    <summary>
      This is a compact test abstract.
    </summary>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <arxiv:doi>10.1000/example</arxiv:doi>
    <link href="http://arxiv.org/abs/1901.01234v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1901.01234v2" rel="related" type="application/pdf"/>
  </entry>
</feed>
"""


class ArxivTests(unittest.TestCase):
    def test_arxiv_entry_to_metadata(self):
        entry = _arxiv_entries(ARXIV_XML)[0]
        result = _arxiv_entry_to_metadata(entry, "arxiv")

        self.assertEqual(result.title, "Example arXiv Paper")
        self.assertEqual(result.authors, ["Alice Smith", "Bob Jones"])
        self.assertEqual(result.year, "2019")
        self.assertEqual(result.doi, "10.1000/example")
        self.assertEqual(result.arxiv_id, "1901.01234v2")
        self.assertEqual(result.data_availability, "Not found")
        self.assertIn({"preprint": "https://arxiv.org/pdf/1901.01234v2"}, result.full_text_links)

    def test_arxiv_entry_to_search(self):
        entry = _arxiv_entries(ARXIV_XML)[0]
        result = _arxiv_entry_to_search(entry)

        self.assertEqual(result.title, "Example arXiv Paper")
        self.assertEqual(result.year, "2019")
        self.assertEqual(result.arxiv_id, "1901.01234v2")
        self.assertEqual(result.source, "arxiv")


if __name__ == "__main__":
    unittest.main()

