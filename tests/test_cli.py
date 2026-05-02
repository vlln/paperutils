import unittest
from contextlib import redirect_stderr
from io import StringIO

from paperutils.cli import build_parser


class CliTests(unittest.TestCase):
    def test_help_contains_only_new_commands(self):
        help_text = build_parser().format_help()
        self.assertIn("get", help_text)
        self.assertIn("find", help_text)
        self.assertIn("explain", help_text)
        self.assertNotIn("resolve", help_text)
        self.assertNotIn("accessions", help_text)
        self.assertNotIn("lookup", help_text)
        self.assertNotIn("search", help_text)

    def test_old_command_is_not_accepted(self):
        parser = build_parser()
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["resolve", "10.1038/example"])


if __name__ == "__main__":
    unittest.main()
