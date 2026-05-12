"""Remote metadata fetchers — public API re-exports."""

from paperutils.fetchers.base import Fetcher
from paperutils.fetchers.arxiv import ArxivFetcher
from paperutils.fetchers.biorxiv import BioRxivFetcher
from paperutils.fetchers.chemrxiv import ChemRxivFetcher
from paperutils.fetchers.crossref import CrossrefFetcher
from paperutils.fetchers.europepmc import EuropePMCFetcher
from paperutils.fetchers.pubmed import PubmedFetcher
from paperutils.fetchers.search import search_biomed, search_cs
from paperutils.fetchers.lookups import lookup_ena, lookup_ncbi, query_gwas_catalog
from paperutils.fetchers.resources import lookup_dataset_resource

BIOMED_FETCHERS: list[Fetcher] = [
    BioRxivFetcher("biorxiv"),
    BioRxivFetcher("medrxiv"),
    ChemRxivFetcher(),
    CrossrefFetcher(),
    EuropePMCFetcher(),
    PubmedFetcher(),
]
CS_FETCHERS: list[Fetcher] = [ArxivFetcher()]
FETCHERS: dict[str, list[Fetcher]] = {
    "biomed": BIOMED_FETCHERS,
    "cs": CS_FETCHERS,
}

__all__ = [
    "Fetcher",
    "ArxivFetcher",
    "BioRxivFetcher",
    "CrossrefFetcher",
    "EuropePMCFetcher",
    "PubmedFetcher",
    "BIOMED_FETCHERS",
    "CS_FETCHERS",
    "FETCHERS",
    "lookup_dataset_resource",
    "lookup_ena",
    "lookup_ncbi",
    "query_gwas_catalog",
    "search_biomed",
    "search_cs",
]
