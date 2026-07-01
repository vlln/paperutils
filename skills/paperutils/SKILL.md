---
name: paperutils
description: Use this skill when the user asks about papers, DOIs, PMIDs, arXiv IDs, datasets, or accessions — anything that requires querying Crossref, Europe PMC, PubMed, arXiv, bioRxiv, ENA, or NCBI.
license: MIT
metadata:
  author: vlln
  version: "0.1.0"
requires:
  bins:
    - paperutils
---

# paperutils

## Trigger Keywords

paper, bibliography, doi, pubmed, arxiv, dataset, accession, bioinformatics, PMID, PMCID, biorxiv, medrxiv, GEO, SRA, ENA, BioProject, Assembly, NCBI, Crossref, Europe PMC, paper lookup, paper search, data availability, supplement, full-text

## Capabilities

### Get a paper dossier

Fetch a comprehensive paper dossier by DOI, PMID, PMCID, arXiv ID, URL (biorxiv, medrxiv, pubmed, arxiv), or title string. The dossier includes metadata, abstract, data availability statement, full-text links, extracted dataset accessions, code repositories, and supplement links.

Two depth levels are available: `fast` returns metadata, abstract, data availability, full-text links, and extracted accessions without verification. `full` (default) adds GWAS Catalog lookup and per-accession ENA/NCBI expansion.

Use `--full-abstract` for the complete abstract text. Use `--domain auto` (default), `biomed`, or `cs` to control query routing.

### Search for papers

Search across biomedical and computer science literature by keyword or title. The `biomed` domain queries Europe PMC and Crossref; the `cs` domain queries the arXiv Atom API. Results default to 5 items; increase with `--limit`.

### Explain dataset accessions

Identify and describe dataset accession numbers from GEO, SRA, ENA, BioProject, Assembly, and other bioinformatics databases. Uses ENA Portal API and NCBI E-utilities. The database source is inferred from the accession prefix pattern when `--db auto` (default).

## Gotchas

- Individual API failures are silently tolerated. The tool returns the best available dossier from sources that respond — partial results are normal, not errors.
- All network calls have a default 4-second timeout per source. Slow or unresponsive endpoints may produce partial dossiers.
- Title queries (text that is not a DOI/PMID/arXiv/URL) first search the biomedical domain, then resolve the top match's DOI for canonical metadata.
- Deep queries (`--depth full`) are significantly slower than `--depth fast` because they expand each accession individually against ENA/NCBI. Default to `fast` unless explicit accession details are needed.
- The tool accepts only `get`, `find`, and `explain` as subcommands. Legacy names (`resolve`, `accessions`, `lookup`, `search`) are not supported.
- Output is YAML-like text by default. Use `--json` when machine-readable output is required.