"""Command-line interface for paperutils."""

from __future__ import annotations

import argparse
import sys

from paperutils import __version__
from paperutils.output import print_accessions, print_lookup, print_metadata, print_search
from paperutils.resolver import accessions, lookup, resolve, search


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(prog="paperutils")
    parser.add_argument("--version", action="version", version=f"paperutils {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="resolve paper metadata")
    resolve_parser.add_argument("identifier")
    resolve_parser.add_argument("--json", action="store_true", help="output JSON")
    resolve_parser.add_argument("--full-abstract", action="store_true", help="do not truncate abstract")
    resolve_parser.add_argument("--domain", choices=("auto", "biomed", "cs"), default="auto")
    resolve_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    accessions_parser = subparsers.add_parser("accessions", help="list related dataset accessions")
    accessions_parser.add_argument("identifier")
    accessions_parser.add_argument("--json", action="store_true", help="output JSON")
    accessions_parser.add_argument("--domain", choices=("auto", "biomed", "cs"), default="auto")
    accessions_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    lookup_parser = subparsers.add_parser("lookup", help="lookup an accession")
    lookup_parser.add_argument("accession")
    lookup_parser.add_argument("--json", action="store_true", help="output JSON")
    lookup_parser.add_argument("--db", choices=("auto", "geo", "ena", "sra", "bioproject", "assembly"), default="auto")
    lookup_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    search_parser = subparsers.add_parser("search", help="search papers")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--json", action="store_true", help="output JSON")
    search_parser.add_argument("--domain", choices=("auto", "biomed", "cs"), default="auto")
    search_parser.add_argument("--timeout", type=float, default=4.0, help="API timeout in seconds")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the paperutils CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "resolve":
            result = resolve(args.identifier, domain=args.domain, timeout=args.timeout)
            print_metadata(result, as_json=args.json, full_abstract=args.full_abstract)
        elif args.command == "accessions":
            result = accessions(args.identifier, domain=args.domain, timeout=args.timeout)
            print_accessions(result, as_json=args.json)
        elif args.command == "lookup":
            result = lookup(args.accession, db=args.db, timeout=args.timeout)
            print_lookup(result, as_json=args.json)
        elif args.command == "search":
            result = search(args.query, limit=args.limit, domain=args.domain, timeout=args.timeout)
            print_search(result, as_json=args.json)
        else:
            parser.error(f"unknown command: {args.command}")
    except Exception as exc:
        print(f"paperutils: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
