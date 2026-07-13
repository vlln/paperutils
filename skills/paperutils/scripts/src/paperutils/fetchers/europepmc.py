"""Europe PMC fetcher and availability-text extraction."""

from __future__ import annotations

import re
from typing import Any

from paperutils.fetchers.base import Fetcher
from paperutils.fetchers.helpers import classify_link, first_matching_title_candidate, split_authors, strip_tags, normalize_space
from paperutils.http import FetchError, get_json, get_text
from paperutils.identifiers import Identifier
from paperutils.models import PaperMetadata


class EuropePMCFetcher(Fetcher):
    """Fetch metadata, data availability, and links from Europe PMC."""

    name = "europepmc"
    search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def can_fetch(self, identifier: Identifier) -> bool:
        return identifier.kind in {"doi", "pmid", "pmcid", "title"}

    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        query = _europepmc_query(identifier)
        data = get_json(
            self.search_url,
            params={
                "query": query,
                "format": "json",
                "pageSize": 5,
                "resultType": "core",
            },
            timeout=timeout,
        )
        results = data.get("resultList", {}).get("result", [])
        if not results:
            raise FetchError("Europe PMC returned no results")
        meta = first_matching_title_candidate(
            identifier,
            (_europepmc_result_to_metadata(result, self.name) for result in results),
            "Europe PMC",
        )
        if not meta.data_availability and meta.pmcid:
            meta.data_availability = fetch_pmc_availability_text(meta.pmcid, timeout)
        return meta


def _europepmc_result_to_metadata(result: dict[str, Any], source: str) -> PaperMetadata:
    meta = PaperMetadata()
    meta.title = result.get("title")
    meta.authors = split_authors(result.get("authorString"))
    meta.journal = result.get("journalTitle")
    meta.year = result.get("pubYear")
    meta.doi = (result.get("doi") or "").lower() or None
    meta.pmid = result.get("pmid")
    meta.pmcid = result.get("pmcid")
    meta.abstract = result.get("abstractText")
    meta.data_availability = result.get("dataAvailability") or None
    for link in _europepmc_links(result):
        meta.full_text_links.append(link)
    meta.add_source(source)
    return meta


def _europepmc_result_to_search(result: dict[str, Any]) -> "SearchResult":
    from paperutils.models import SearchResult

    return SearchResult(
        title=result.get("title") or "Untitled",
        year=result.get("pubYear"),
        journal=result.get("journalTitle"),
        doi=(result.get("doi") or "").lower() or None,
        pmid=result.get("pmid"),
        pmcid=result.get("pmcid"),
        source="europepmc",
    )


def _europepmc_query(identifier: Identifier) -> str:
    if identifier.kind == "doi":
        return f'DOI:"{identifier.value}"'
    if identifier.kind == "pmid":
        return f"EXT_ID:{identifier.value} AND SRC:MED"
    if identifier.kind == "pmcid":
        return f"PMCID:{identifier.value}"
    return identifier.value


def _europepmc_links(result: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    pmcid = result.get("pmcid")
    if pmcid:
        links.append({"pmc": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"})
    doi = result.get("doi")
    if doi:
        links.append({"publisher": f"https://doi.org/{doi}"})
    for item in result.get("fullTextUrlList", {}).get("fullTextUrl", []) or []:
        url = item.get("url")
        if url:
            label = classify_link(
                url,
                default=(item.get("site") or "full_text").lower().replace(" ", "_"),
                content_type=item.get("documentStyle"),
                intended_application=item.get("availability"),
            )
            links.append({label: url})
    return links


# -- PMC availability-text extraction ----------------------------------------


def fetch_pmc_availability_text(pmcid: str, timeout: float) -> str | None:
    """Extract data/code availability from PMC full-text XML via NCBI E-utilities."""
    numeric_id = pmcid.removeprefix("PMC").removeprefix("pmc")
    if not numeric_id.isdigit():
        return None
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={numeric_id}&retmode=xml"
    try:
        xml_str = get_text(url, timeout=timeout)
    except FetchError:
        return None
    return _extract_availability_from_xml(xml_str)


def _extract_availability_from_xml(xml_str: str) -> str | None:
    text = re.sub(r"<[^>]+>", " ", xml_str)
    text = re.sub(r"\s+", " ", text).strip()
    lower = text.lower()

    start_markers = (
        "data availability statement",
        "data availability",
        "data and code availability",
        "data and materials availability",
        "availability of data and materials",
        "availability of data",
    )
    stop_markers = (
        "code availability",
        "supplementary materials",
        "supplementary information",
        "acknowledgements",
        "author contributions",
        "competing interests",
        "conflict of interest",
        "ethics declarations",
        "footnotes",
        "references",
    )

    candidates = []
    for marker in start_markers:
        start = 0
        while True:
            start = lower.find(marker, start)
            if start == -1:
                break
            end = _first_marker_position(lower, stop_markers, start + len(marker) + 1)
            section = text[start:end].strip() if end is not None else text[start:].strip()
            if section and len(section) > len(marker) + 5:
                candidates.append(section[:4000])
            start += len(marker)

    if not candidates:
        return None
    return max(candidates, key=len)


def _first_marker_position(text: str, markers: tuple[str, ...], start: int) -> int | None:
    for marker in markers:
        pattern = re.compile(r"(?:[.;]\s+|\.\s+|\n)\s*" + re.escape(marker), re.IGNORECASE)
        m = pattern.search(text, start)
        if m:
            return m.start()
    return None
