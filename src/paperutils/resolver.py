"""High-level operations for the paperutils CLI."""

from __future__ import annotations

import concurrent.futures
from typing import Iterable

from paperutils.accessions import classify_accession, extract_accessions
from paperutils.fetchers import FETCHERS, lookup_ena, lookup_ncbi, query_gwas_catalog, search_biomed, search_cs
from paperutils.identifiers import Identifier, infer_domain, parse_identifier
from paperutils.models import Accession, LookupResult, PaperMetadata, SearchResult


def resolve(identifier_text: str, domain: str = "auto", timeout: float = 4.0) -> PaperMetadata:
    """Resolve a paper identifier into merged metadata."""

    identifier = parse_identifier(identifier_text)
    selected_domain = infer_domain(identifier, domain)
    fetchers = [fetcher for fetcher in FETCHERS.get(selected_domain, []) if fetcher.can_fetch(identifier)]
    if not fetchers and identifier.kind == "title":
        fetchers = [fetcher for fetcher in FETCHERS.get("biomed", []) if fetcher.can_fetch(identifier)]
    if not fetchers:
        raise ValueError(f"unsupported identifier/domain combination: {identifier.kind}/{selected_domain}")

    merged = PaperMetadata()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(fetchers))
    futures = {
        executor.submit(fetcher.fetch, identifier, timeout): fetcher.name
        for fetcher in fetchers
    }
    done, pending = concurrent.futures.wait(futures, timeout=timeout + 0.5)
    for future in done:
        try:
            partial = future.result(timeout=0)
        except Exception:
            continue
        _merge_metadata(merged, partial)
    for future in pending:
        future.cancel()
    executor.shutdown(wait=False, cancel_futures=True)

    if not merged.sources:
        raise RuntimeError("no metadata sources returned a usable result")
    if not merged.data_availability:
        merged.data_availability = "Not found"
    merged.full_text_links = _dedupe_links(merged.full_text_links)
    return merged


def accessions(identifier_text: str, domain: str = "auto", timeout: float = 4.0) -> list[Accession]:
    """Resolve a paper and list related dataset accessions."""

    paper = resolve(identifier_text, domain=domain, timeout=timeout)
    found = extract_accessions(paper.data_availability)
    found.extend(query_gwas_catalog(paper, timeout=timeout))
    return _dedupe_accessions(found)


def lookup(accession: str, db: str = "auto", timeout: float = 4.0) -> LookupResult:
    """Lookup one accession in ENA or NCBI."""

    clean = accession.strip()
    kind = classify_accession(clean)
    candidates = _lookup_candidates(kind, db)
    for candidate in candidates:
        if candidate == "ena":
            result = lookup_ena(clean, timeout=timeout)
        else:
            result = lookup_ncbi(clean, candidate, timeout=timeout)
        if result:
            return result
    return LookupResult(accession=clean, type=kind, status="Not found")


def search(query: str, limit: int = 5, domain: str = "auto", timeout: float = 4.0) -> list[SearchResult]:
    """Search papers by title or keyword."""

    selected_domain = "biomed" if domain == "auto" else domain
    if selected_domain == "cs":
        return search_cs(query, limit=limit, timeout=timeout)
    if selected_domain != "biomed":
        raise ValueError(f"search domain is not implemented yet: {selected_domain}")
    return search_biomed(query, limit=limit, timeout=timeout)


def _merge_metadata(target: PaperMetadata, source: PaperMetadata) -> None:
    # Field precedence is encoded by only filling empty values, except Europe PMC's
    # data availability is authoritative and PubMed/Europe PMC abstracts may fill gaps.
    for field_name in ("title", "journal", "year", "doi", "arxiv_id", "pmid", "pmcid"):
        if not getattr(target, field_name) and getattr(source, field_name):
            setattr(target, field_name, getattr(source, field_name))

    if not target.authors and source.authors:
        target.authors = source.authors

    if source.abstract and (not target.abstract or "europepmc" in source.sources):
        target.abstract = source.abstract

    if "europepmc" in source.sources and source.data_availability:
        target.data_availability = source.data_availability

    target.full_text_links.extend(source.full_text_links)
    for source_name in source.sources:
        target.add_source(source_name)


def _dedupe_links(links: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    unique = []
    for link in links:
        if not link:
            continue
        key, value = next(iter(link.items()))
        marker = (key, value)
        if marker not in seen:
            unique.append({key: value})
            seen.add(marker)
    return unique


def _dedupe_accessions(items: Iterable[Accession]) -> list[Accession]:
    seen = set()
    unique = []
    for item in items:
        marker = item.accession.upper()
        if marker not in seen:
            unique.append(item)
            seen.add(marker)
    return unique


def _lookup_candidates(kind: str, requested_db: str) -> list[str]:
    if requested_db != "auto":
        return [_normalize_ncbi_db(requested_db)]
    if kind in {"ENA", "SRA"}:
        return ["ena", "sra"]
    if kind == "GEO":
        return ["gds"]
    if kind == "BioProject":
        return ["bioproject"]
    if kind == "Assembly":
        return ["assembly"]
    return ["ena", "sra", "gds", "bioproject"]


def _normalize_ncbi_db(db: str) -> str:
    mapping = {
        "geo": "gds",
        "sra": "sra",
        "ena": "ena",
        "bioproject": "bioproject",
        "assembly": "assembly",
    }
    return mapping.get(db, db)
