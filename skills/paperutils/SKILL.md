---
name: paperutils
description: Run paperutils CLI commands (get, find, explain) to fetch paper dossiers, search for papers, or explain dataset accessions for biomedical and CS papers. Use when the user asks about papers, DOIs, PMIDs, arXiv IDs, datasets, or accessions — anything that requires querying Crossref, Europe PMC, PubMed, arXiv, bioRxiv, ENA, or NCBI.
metadata:
  skit:
    version: 0.1.0
    requires:
      bins:
        - paperutils
    keywords:
      - paper
      - bibliography
      - doi
      - pubmed
      - arxiv
      - dataset
      - accession
      - bioinformatics
---

# paperutils

## When To Use

Use when the user asks to:
- Look up a paper by DOI, PMID, PMCID, arXiv ID, URL, or title
- Search for papers by keyword or title
- Identify or explain dataset accession numbers (GEO, SRA, ENA, BioProject, Assembly, etc.)
- Get a paper's abstract, data availability statement, or code repositories
- Find full-text links or supplement files for a paper

## Commands

### `get` — Paper dossier

```bash
paperutils get <identifier> [--depth fast|full] [--json] [--full-abstract] [--domain auto|biomed|cs] [--timeout SECONDS]
```

Accepts DOI, PMID, PMCID, arXiv ID, URL (biorxiv/medrxiv/pubmed/arxiv), or a title string.

`--depth fast`: metadata, abstract, data availability, full-text links, extracted accessions (no verification).
`--depth full` (default): fast + GWAS Catalog lookup + per-accession ENA/NCBI expansion.
`--full-abstract`: print full abstract instead of truncated.

### `find` — Search papers

```bash
paperutils find <query> [--limit N] [--json] [--domain auto|biomed|cs] [--timeout SECONDS]
```

`--domain biomed`: Europe PMC + Crossref.
`--domain cs`: arXiv Atom API.
Default limit is 5.

### `explain` — Dataset/accession lookup

```bash
paperutils explain <accession> [--db auto|geo|ena|sra|bioproject|assembly] [--json] [--timeout SECONDS]
```

Supports ENA Portal API and NCBI E-utilities. `--db auto` infers the source from the accession prefix pattern.

## Rules

- The tool has zero Python dependencies — it works anywhere Python 3.10+ is installed.
- Run from the checkout: `./paperutils` (adds `src/` to sys.path). Installed: `paperutils`.
- Default output is YAML-like; `--json` for machine-readable output.
- Individual API failures are silently tolerated — the tool returns the best dossier from sources that respond.
- All network calls have a default 4s timeout per source, configurable with `--timeout`.
- Title queries (text that isn't a DOI/PMID/arXiv/URL) first search biomed, then resolve the top match's DOI for canonical metadata.
- Never use legacy command names: `resolve`, `accessions`, `lookup`, `search` are rejected.

## Output

YAML-like text by default; JSON with `--json`. Paper dossiers include: title, authors, journal/year, DOIs, abstract, data availability statement, supplement links, code repos (GitHub), extracted dataset accessions, and full-text links.
