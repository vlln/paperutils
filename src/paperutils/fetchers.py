"""Remote metadata fetchers.

The first implementation focuses on biomedical sources. Fetchers return partial
``PaperMetadata`` objects so the resolver can merge whichever sources succeed.
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any

from paperutils.http import FetchError, get_json, get_text
from paperutils.identifiers import Identifier
from paperutils.models import Accession, LookupResult, PaperMetadata, SearchResult


class Fetcher(ABC):
    """Base class for metadata fetchers."""

    name: str

    @abstractmethod
    def can_fetch(self, identifier: Identifier) -> bool:
        """Return whether this fetcher can query the identifier directly."""

    @abstractmethod
    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        """Fetch metadata for an identifier."""


class CrossrefFetcher(Fetcher):
    """Fetch DOI/title metadata from Crossref."""

    name = "crossref"
    base_url = "https://api.crossref.org/works"

    def can_fetch(self, identifier: Identifier) -> bool:
        return identifier.kind in {"doi", "title"}

    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        if identifier.kind == "doi":
            url = f"{self.base_url}/{identifier.value}"
            message = get_json(url, timeout=timeout).get("message", {})
            return _crossref_work_to_metadata(message, self.name)

        data = get_json(
            self.base_url,
            params={"query.title": identifier.value, "rows": 1},
            timeout=timeout,
        )
        items = data.get("message", {}).get("items", [])
        if not items:
            raise FetchError("Crossref returned no results")
        return _crossref_work_to_metadata(items[0], self.name)


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
                "pageSize": 1,
                "resultType": "core",
            },
            timeout=timeout,
        )
        results = data.get("resultList", {}).get("result", [])
        if not results:
            raise FetchError("Europe PMC returned no results")
        return _europepmc_result_to_metadata(results[0], self.name)


class PubmedFetcher(Fetcher):
    """Fetch PubMed metadata via NCBI E-utilities."""

    name = "pubmed"
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def can_fetch(self, identifier: Identifier) -> bool:
        return identifier.kind in {"doi", "pmid", "pmcid", "title"}

    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        pmid = identifier.value if identifier.kind == "pmid" else self._search_pmid(identifier, timeout)
        xml_text = get_text(
            self.efetch_url,
            params={"db": "pubmed", "id": pmid, "retmode": "xml"},
            timeout=timeout,
        )
        return _pubmed_xml_to_metadata(xml_text, self.name)

    def _search_pmid(self, identifier: Identifier, timeout: float) -> str:
        term = {
            "doi": f"{identifier.value}[doi]",
            "pmcid": identifier.value,
            "title": identifier.value,
        }.get(identifier.kind, identifier.value)
        xml_text = get_text(
            self.esearch_url,
            params={"db": "pubmed", "term": term, "retmode": "xml", "retmax": 1},
            timeout=timeout,
        )
        root = ET.fromstring(xml_text)
        pmid = root.findtext(".//Id")
        if not pmid:
            raise FetchError("PubMed returned no PMID")
        return pmid


class ArxivFetcher(Fetcher):
    """Fetch arXiv metadata through the public Atom API."""

    name = "arxiv"
    api_url = "https://export.arxiv.org/api/query"
    atom_ns = {"atom": "http://www.w3.org/2005/Atom"}
    arxiv_ns = {"arxiv": "http://arxiv.org/schemas/atom"}

    def can_fetch(self, identifier: Identifier) -> bool:
        return identifier.kind in {"arxiv", "title"}

    def fetch(self, identifier: Identifier, timeout: float) -> PaperMetadata:
        params = {"max_results": 1}
        if identifier.kind == "arxiv":
            params["id_list"] = identifier.value
        else:
            params["search_query"] = f'ti:"{identifier.value}"'
        xml_text = get_text(self.api_url, params=params, timeout=timeout)
        entries = _arxiv_entries(xml_text)
        if not entries:
            raise FetchError("arXiv returned no results")
        return _arxiv_entry_to_metadata(entries[0], self.name)


BIOMED_FETCHERS: list[Fetcher] = [CrossrefFetcher(), EuropePMCFetcher(), PubmedFetcher()]
CS_FETCHERS: list[Fetcher] = [ArxivFetcher()]
FETCHERS: dict[str, list[Fetcher]] = {
    "biomed": BIOMED_FETCHERS,
    "cs": CS_FETCHERS,
}


def search_biomed(query: str, limit: int, timeout: float) -> list[SearchResult]:
    """Search papers with Europe PMC first, then Crossref as fallback."""

    try:
        data = get_json(
            EuropePMCFetcher.search_url,
            params={
                "query": query,
                "format": "json",
                "pageSize": max(1, limit),
                "resultType": "lite",
            },
            timeout=timeout,
        )
        results = data.get("resultList", {}).get("result", [])
        if results:
            return [_europepmc_result_to_search(item) for item in results[:limit]]
    except FetchError:
        pass

    data = get_json(
        CrossrefFetcher.base_url,
        params={"query.title": query, "rows": max(1, limit)},
        timeout=timeout,
    )
    return [_crossref_work_to_search(item) for item in data.get("message", {}).get("items", [])[:limit]]


def search_cs(query: str, limit: int, timeout: float) -> list[SearchResult]:
    """Search arXiv papers by title or keyword."""

    xml_text = get_text(
        ArxivFetcher.api_url,
        params={
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max(1, limit),
            "sortBy": "relevance",
            "sortOrder": "descending",
        },
        timeout=timeout,
    )
    return [_arxiv_entry_to_search(entry) for entry in _arxiv_entries(xml_text)[:limit]]


def query_gwas_catalog(paper: PaperMetadata, timeout: float) -> list[Accession]:
    """Query GWAS Catalog associations by PMID when available."""

    if not paper.pmid:
        return []
    url = "https://www.ebi.ac.uk/gwas/rest/api/studies/search/findByPubmedId"
    try:
        data = get_json(url, params={"pubmedId": paper.pmid}, timeout=timeout)
    except FetchError:
        return []
    studies = data.get("_embedded", {}).get("studies", [])
    accessions = []
    for study in studies:
        accession = study.get("accessionId")
        if accession:
            trait = study.get("diseaseTrait", {}).get("trait") or study.get("initialSampleSize") or ""
            accessions.append(Accession("GWAS", accession, str(trait)))
    return accessions


def lookup_ena(accession: str, timeout: float) -> LookupResult | None:
    """Lookup an accession in the ENA Portal API."""

    fields = [
        "study_accession",
        "secondary_study_accession",
        "sample_accession",
        "run_accession",
        "experiment_accession",
        "scientific_name",
        "study_title",
        "experiment_title",
        "submitted_ftp",
        "first_public",
        "status",
    ]
    try:
        text = get_text(
            "https://www.ebi.ac.uk/ena/portal/api/search",
            params={
                "result": "read_run",
                "query": f'accession="{accession}"',
                "fields": ",".join(fields),
                "format": "tsv",
                "limit": 1,
            },
            timeout=timeout,
        )
    except FetchError:
        return None
    rows = [line.split("\t") for line in text.splitlines() if line.strip()]
    if len(rows) < 2:
        return None
    header, row = rows[0], rows[1]
    data = dict(zip(header, row))
    return LookupResult(
        accession=accession,
        title=data.get("study_title") or data.get("experiment_title"),
        organism=data.get("scientific_name"),
        type="ENA read run/study",
        submitted=data.get("first_public"),
        status=data.get("status"),
        source="ena",
    )


def lookup_ncbi(accession: str, db: str, timeout: float) -> LookupResult | None:
    """Lookup an accession in NCBI using esearch + esummary."""

    try:
        xml_text = get_text(
            PubmedFetcher.esearch_url,
            params={"db": db, "term": accession, "retmode": "xml", "retmax": 1},
            timeout=timeout,
        )
        root = ET.fromstring(xml_text)
        uid = root.findtext(".//Id")
        if not uid:
            return None
        summary = get_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": db, "id": uid, "retmode": "json"},
            timeout=timeout,
        )
    except (FetchError, ET.ParseError):
        return None
    item = summary.get("result", {}).get(uid, {})
    return LookupResult(
        accession=accession,
        title=item.get("title") or item.get("expacc") or item.get("bioproject"),
        organism=item.get("organism") or item.get("taxname"),
        type=db,
        samples=_sample_count(item.get("runs") or item.get("samples")),
        submitted=item.get("submissiondate") or item.get("createdate"),
        status=item.get("status"),
        source=f"ncbi:{db}",
        extra={k: str(v) for k, v in item.items() if isinstance(v, (str, int))},
    )


def _crossref_work_to_metadata(work: dict[str, Any], source: str) -> PaperMetadata:
    meta = PaperMetadata()
    meta.title = _first(work.get("title"))
    meta.authors = _crossref_authors(work.get("author", []))
    meta.journal = _first(work.get("container-title"))
    meta.year = _crossref_year(work)
    meta.doi = work.get("DOI", "").lower() or None
    abstract = work.get("abstract")
    if abstract:
        meta.abstract = _strip_tags(abstract)
    for link in work.get("link", []) or []:
        url = link.get("URL")
        if url:
            meta.full_text_links.append({"publisher": url})
    if work.get("URL"):
        meta.full_text_links.append({"publisher": work["URL"]})
    meta.add_source(source)
    return meta


def _crossref_work_to_search(work: dict[str, Any]) -> SearchResult:
    return SearchResult(
        title=_first(work.get("title")) or "Untitled",
        year=_crossref_year(work),
        journal=_first(work.get("container-title")),
        doi=(work.get("DOI") or "").lower() or None,
        source="crossref",
    )


def _europepmc_result_to_metadata(result: dict[str, Any], source: str) -> PaperMetadata:
    meta = PaperMetadata()
    meta.title = result.get("title")
    meta.authors = _split_authors(result.get("authorString"))
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


def _europepmc_result_to_search(result: dict[str, Any]) -> SearchResult:
    return SearchResult(
        title=result.get("title") or "Untitled",
        year=result.get("pubYear"),
        journal=result.get("journalTitle"),
        doi=(result.get("doi") or "").lower() or None,
        pmid=result.get("pmid"),
        pmcid=result.get("pmcid"),
        source="europepmc",
    )


def _pubmed_xml_to_metadata(xml_text: str, source: str) -> PaperMetadata:
    root = ET.fromstring(xml_text)
    article = root.find(".//PubmedArticle")
    if article is None:
        raise FetchError("PubMed returned no article")
    meta = PaperMetadata()
    meta.pmid = article.findtext(".//MedlineCitation/PMID")
    meta.title = _xml_text(article.find(".//ArticleTitle"))
    meta.journal = article.findtext(".//Journal/Title") or article.findtext(".//Journal/ISOAbbreviation")
    meta.year = (
        article.findtext(".//JournalIssue/PubDate/Year")
        or article.findtext(".//ArticleDate/Year")
        or article.findtext(".//PubMedPubDate/Year")
    )
    meta.abstract = _abstract_from_pubmed(article)
    meta.authors = _pubmed_authors(article)
    for article_id in article.findall("./PubmedData/ArticleIdList/ArticleId"):
        id_type = (article_id.attrib.get("IdType") or "").lower()
        value = (article_id.text or "").strip()
        if id_type == "doi":
            meta.doi = value.lower()
        elif id_type == "pmc":
            meta.pmcid = value.upper()
    meta.add_source(source)
    return meta


def _arxiv_entries(xml_text: str) -> list[ET.Element]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise FetchError("invalid arXiv Atom response") from exc
    return root.findall("atom:entry", ArxivFetcher.atom_ns)


def _arxiv_entry_to_metadata(entry: ET.Element, source: str) -> PaperMetadata:
    meta = PaperMetadata()
    meta.title = _normalize_space(_find_atom_text(entry, "title"))
    meta.authors = [
        _normalize_space(author.findtext("atom:name", namespaces=ArxivFetcher.atom_ns))
        for author in entry.findall("atom:author", ArxivFetcher.atom_ns)
    ]
    meta.authors = [author for author in meta.authors if author]
    meta.year = _year_from_date(_find_atom_text(entry, "published") or _find_atom_text(entry, "updated"))
    meta.abstract = _normalize_space(_find_atom_text(entry, "summary"))
    meta.arxiv_id = _arxiv_id_from_entry(entry)
    doi = entry.findtext("arxiv:doi", namespaces=ArxivFetcher.arxiv_ns)
    meta.doi = doi.lower() if doi else None
    if meta.arxiv_id:
        meta.full_text_links.append({"preprint": f"https://arxiv.org/pdf/{meta.arxiv_id}"})
        meta.full_text_links.append({"arxiv": f"https://arxiv.org/abs/{meta.arxiv_id}"})
    for link in entry.findall("atom:link", ArxivFetcher.atom_ns):
        href = link.attrib.get("href")
        title = link.attrib.get("title")
        link_type = link.attrib.get("type")
        if href and (title == "pdf" or link_type == "application/pdf"):
            meta.full_text_links.append({"preprint": href})
    meta.data_availability = "Not found"
    meta.add_source(source)
    return meta


def _arxiv_entry_to_search(entry: ET.Element) -> SearchResult:
    return SearchResult(
        title=_normalize_space(_find_atom_text(entry, "title")) or "Untitled",
        year=_year_from_date(_find_atom_text(entry, "published") or _find_atom_text(entry, "updated")),
        doi=(entry.findtext("arxiv:doi", namespaces=ArxivFetcher.arxiv_ns) or "").lower() or None,
        arxiv_id=_arxiv_id_from_entry(entry),
        source="arxiv",
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
        site = (item.get("site") or "full_text").lower().replace(" ", "_")
        if url:
            links.append({site: url})
    return links


def _crossref_authors(authors: list[dict[str, Any]]) -> list[str]:
    names = []
    for author in authors:
        parts = [author.get("given"), author.get("family")]
        name = " ".join(part for part in parts if part)
        if name:
            names.append(name)
    return names


def _crossref_year(work: dict[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "published", "issued"):
        date_parts = work.get(key, {}).get("date-parts")
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return None


def _split_authors(author_string: str | None) -> list[str]:
    if not author_string:
        return []
    return [part.strip() for part in author_string.rstrip(".").split(",") if part.strip()]


def _pubmed_authors(article: ET.Element) -> list[str]:
    authors = []
    for author in article.findall(".//AuthorList/Author"):
        collective = author.findtext("CollectiveName")
        if collective:
            authors.append(collective)
            continue
        last = author.findtext("LastName")
        fore = author.findtext("ForeName") or author.findtext("Initials")
        name = " ".join(part for part in (fore, last) if part)
        if name:
            authors.append(name)
    return authors


def _abstract_from_pubmed(article: ET.Element) -> str | None:
    parts = []
    for node in article.findall(".//Abstract/AbstractText"):
        label = node.attrib.get("Label")
        text = _xml_text(node)
        if text and label:
            parts.append(f"{label}: {text}")
        elif text:
            parts.append(text)
    return " ".join(parts) or None


def _xml_text(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    text = "".join(node.itertext())
    return " ".join(html.unescape(text).split()) or None


def _strip_tags(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(text)).split())


def _first(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return None


def _sample_count(value: Any) -> str | None:
    if isinstance(value, list):
        return str(len(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value:
        return value
    return None


def _find_atom_text(entry: ET.Element, name: str) -> str | None:
    return entry.findtext(f"atom:{name}", namespaces=ArxivFetcher.atom_ns)


def _arxiv_id_from_entry(entry: ET.Element) -> str | None:
    entry_id = _find_atom_text(entry, "id")
    if not entry_id:
        return None
    value = entry_id.rstrip("/").rsplit("/", 1)[-1]
    return value.replace(".pdf", "")


def _year_from_date(value: str | None) -> str | None:
    if value and len(value) >= 4 and value[:4].isdigit():
        return value[:4]
    return None


def _normalize_space(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.split())
