"""Command-line interface for paperutils."""

from __future__ import annotations

import argparse
import sys

from paperutils import __version__
from paperutils.output import print_explanation, print_find_results, print_paper_record
from paperutils.resolver import explain_accession, find_papers, get_paper


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(prog="paperutils")
    parser.add_argument("--version", action="version", version=f"paperutils {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get", help="get a complete paper dossier")
    get_parser.add_argument("identifier")
    get_parser.add_argument("--depth", choices=("fast", "full"), default="full")
    get_parser.add_argument("--json", action="store_true", help="output JSON")
    get_parser.add_argument("--full-abstract", action="store_true", help="do not truncate abstract")
    get_parser.add_argument("--domain", choices=("auto", "biomed", "cs"), default="auto")
    get_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    find_parser = subparsers.add_parser("find", help="find paper candidates")
    find_parser.add_argument("query")
    find_parser.add_argument("--limit", type=int, default=5)
    find_parser.add_argument("--json", action="store_true", help="output JSON")
    find_parser.add_argument("--domain", choices=("auto", "biomed", "cs", "physics"), default="auto")
    find_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    explain_parser = subparsers.add_parser("explain", help="explain a dataset accession")
    explain_parser.add_argument("accession")
    explain_parser.add_argument("--json", action="store_true", help="output JSON")
    explain_parser.add_argument(
        "--db",
        choices=("auto", "geo", "ena", "sra", "bioproject", "assembly"),
        default="auto",
    )
    explain_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the paperutils CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "get":
            result = get_paper(
                args.identifier,
                depth=args.depth,
                domain=args.domain,
                timeout=args.timeout,
            )
            print_paper_record(result, as_json=args.json, full_abstract=args.full_abstract)
        elif args.command == "find":
            result = find_papers(args.query, limit=args.limit, domain=args.domain, timeout=args.timeout)
            print_find_results(result, as_json=args.json)
        elif args.command == "explain":
            result = explain_accession(args.accession, db=args.db, timeout=args.timeout)
            print_explanation(result, as_json=args.json)
        else:
            parser.error(f"unknown command: {args.command}")
    except Exception as exc:
        print(f"paperutils: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
