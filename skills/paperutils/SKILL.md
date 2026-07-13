---
name: paperutils
description: Use this skill when the user asks about papers, DOIs, PMIDs, arXiv IDs, datasets, or accessions — anything that requires querying Crossref, Europe PMC, PubMed, arXiv, bioRxiv, ENA, or NCBI.
license: MIT
metadata:
  author: vlln
  version: "0.1.0"
---

# paperutils

## Setup

The tool is embedded in this skill directory. Requires Python 3.9+. Run it as:

```
python3 <skill-dir>/scripts/paperutils <subcommand> ...
```

If `paperutils` is already on PATH (e.g. from a pip install), prefer that over the embedded copy.

## Trigger Keywords

paper, bibliography, doi, pubmed, arxiv, dataset, accession, bioinformatics, PMID, PMCID, biorxiv, medrxiv, GEO, SRA, ENA, BioProject, Assembly, NCBI, Crossref, Europe PMC, paper lookup, paper search, data availability, supplement, full-text

## Capabilities

### Get a paper dossier

Run `paperutils get <identifier>` to fetch a dossier for a paper by DOI, PMID, PMCID, arXiv ID, URL, or title. The dossier includes metadata, abstract, data availability statement, full-text links, extracted dataset accessions, code repositories, and supplement links.

Default is `--depth full`, which expands each accession individually and checks GWAS Catalog. Use `--depth fast` when you only need metadata and extracted accessions without verification — it is significantly faster.

Use `--full-abstract` for the complete abstract text. Use `--json` for machine-readable output.

### Search for papers

Run `paperutils find <query>` to search for papers by keyword or title. Use `--domain biomed` for biomedical literature, `--domain cs` for computer science, or `--domain auto` (default). Defaults to 5 results; increase with `--limit N`.

After finding candidates, run `paperutils get` on the best match to get the full dossier.

### Explain dataset accessions

Run `paperutils explain <accession>` to identify and describe an accession number. The database source is inferred from the accession prefix when `--db auto` (default). Override with `--db geo|ena|sra|bioproject|assembly`.

## Gotchas

- Partial dossiers are normal. Individual API sources may fail (timeout, HTTP errors) — the tool returns the best available data from responding sources. When *all* sources fail, the error message includes the specific reason for each (e.g. "pubmed: timed out; crossref: HTTP 429"). Do not retry or report partial results as errors.
- `--depth full` is significantly slower than `--depth fast`. Default to `fast` unless you need verified accession details.
- Title queries (plain text, not a DOI/PMID/arXiv/URL) first search the biomedical domain, then resolve the top match. For known identifiers, pass the identifier directly for faster, more accurate results.
- The subcommands are `get`, `find`, and `explain` only. Legacy names are not supported.
- Output is YAML-like text by default. Use `--json` when you need to parse the result programmatically.