"""ChemRxiv fetcher via Crossref (with optional Cambridge Open Engage API enrichment)."""

from __future__ import annotations

from paperutils.fetchers.base import Fetcher
from paperutils.fetchers.helpers import classify_link, first, split_authors, year_from_date, strip_tags
from paperutils.http import FetchError, get_json
from paperutils.identifiers import Identifier
from paperutils.models import PaperMetadata

CHEMRXIV_DOI_PREFIX = "10.26434"


class ChemRxivFetcher(Fetcher):
    """Fetch chemRxiv preprint metadata.

    Primary data source is Crossref (chemRxiv DOIs are registered there).
    The Cambridge Open Engage API can provide richer data (abstract,
    categories, asset URLs) but is often blocked by Cloudflare.
    """

    name = "chemrxiv"

    def can_fetch(self, identifier: Identifier) -> bool:
        if identifier.kind != "doi":
            return False
        return identifier.value.startswith(f"{CHEMRXIV_DOI_PREFIX}/")

    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        # Crossref is the reliable data source for chemRxiv DOIs.
        data = get_json(
            f"https://api.crossref.org/works/{identifier.value}",
            timeout=timeout,
        )
        message = data.get("message", {})
        if not message:
            raise FetchError("Crossref returned no data for this DOI")
        meta = _crossref_to_metadata(message)
        meta.preprint_server = "chemrxiv"
        meta.add_source(self.name)
        return meta


def _crossref_to_metadata(message: dict) -> PaperMetadata:
    meta = PaperMetadata()
    meta.title = first(message.get("title"))
    meta.authors = split_authors(
        ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in message.get("author", []) or []
        )
    ) or None
    meta.year = year_from_date(
        str(message.get("posted", {}).get("date-parts", [[None]])[0][0])
    )
    meta.doi = (message.get("DOI") or "").lower() or None
    abstract = message.get("abstract")
    if abstract:
        meta.abstract = strip_tags(abstract)
    meta.journal = "chemRxiv"
    meta.data_availability = "Not found"
    for link in message.get("link", []) or []:
        url = link.get("URL")
        if url:
            meta.full_text_links.append({
                classify_link(
                    url,
                    default="publisher",
                    content_type=link.get("content-type"),
                    intended_application=link.get("intended-application"),
                ): url
            })
    if message.get("resource", {}).get("primary", {}).get("URL"):
        meta.full_text_links.append({
            "publisher": message["resource"]["primary"]["URL"]
        })
    return meta