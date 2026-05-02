"""Output formatting helpers."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from paperutils.models import Accession, LookupResult, PaperMetadata, SearchResult


def print_metadata(meta: PaperMetadata, *, as_json: bool = False, full_abstract: bool = False) -> None:
    """Print resolved paper metadata."""

    data = _metadata_dict(meta, full_abstract=full_abstract)
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    for key in (
        "title",
        "authors",
        "journal",
        "year",
        "doi",
        "arxiv_id",
        "pmid",
        "pmcid",
        "abstract",
        "data_availability",
    ):
        print(f"{key}: {_format_value(data.get(key))}")
    print("full_text_links:")
    links = data.get("full_text_links") or []
    if links:
        for link in links:
            name, url = next(iter(link.items()))
            print(f"  - {name}: {url}")
    else:
        print("  []")
    print(f"sources: {', '.join(meta.sources)}")


def print_accessions(items: list[Accession], *, as_json: bool = False) -> None:
    """Print accession table."""

    if as_json:
        print(json.dumps([dataclasses.asdict(item) for item in items], ensure_ascii=False, indent=2))
        return
    print(f"{'type':<12} {'accession':<16} description")
    for item in items:
        print(f"{item.type:<12} {item.accession:<16} {item.description}")


def print_lookup(result: LookupResult, *, as_json: bool = False) -> None:
    """Print accession lookup result."""

    data = dataclasses.asdict(result)
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    for key in ("accession", "title", "organism", "type", "samples", "submitted", "status", "source"):
        print(f"{key + ':':<12} {_format_value(data.get(key))}")


def print_search(results: list[SearchResult], *, as_json: bool = False) -> None:
    """Print search result list."""

    if as_json:
        print(json.dumps([dataclasses.asdict(item) for item in results], ensure_ascii=False, indent=2))
        return
    print(f"{'#':<3} {'year':<6} {'pmid':<10} {'doi/arxiv':<32} title")
    for index, item in enumerate(results, start=1):
        identifier = item.doi or item.arxiv_id
        print(
            f"{index:<3} {_format_value(item.year):<6} "
            f"{_format_value(item.pmid):<10} {_format_value(identifier):<32} {item.title}"
        )


def _metadata_dict(meta: PaperMetadata, *, full_abstract: bool) -> dict[str, Any]:
    authors = _format_authors(meta.authors)
    abstract = meta.abstract or "Not found"
    if not full_abstract and len(abstract) > 500:
        abstract = abstract[:497].rstrip() + "..."
    return {
        "title": meta.title or "Not found",
        "authors": authors,
        "journal": meta.journal or "Not found",
        "year": meta.year or "Not found",
        "doi": meta.doi or "Not found",
        "arxiv_id": meta.arxiv_id or "Not found",
        "pmid": meta.pmid or "Not found",
        "pmcid": meta.pmcid or "Not found",
        "abstract": abstract,
        "data_availability": meta.data_availability or "Not found",
        "full_text_links": meta.full_text_links,
        "sources": meta.sources,
    }


def _format_authors(authors: list[str]) -> str:
    if not authors:
        return "Not found"
    if len(authors) <= 6:
        return ", ".join(authors)
    return f"{', '.join(authors[:2])}, et al. ({len(authors)} authors)"


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return "Not found"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)
