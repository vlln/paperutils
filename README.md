# paperutils

`paperutils` is a dependency-free Python CLI for resolving paper metadata and
finding related dataset accessions. It currently focuses on biomedical papers
and uses only the Python standard library.

## Run From Source

```bash
./paperutils --help
./paperutils resolve 10.1038/s41586-020-2649-2
./paperutils accessions PMID:32939066
./paperutils lookup GSE100
./paperutils search "numpy array programming" --limit 3
./paperutils resolve arXiv:1901.01234
./paperutils resolve 10.1101/2019.12.31.892091
```

The source checkout runner adds `src/` to `sys.path`, so no installation step is
required.

## Install Locally

```bash
python3 -m pip install .
paperutils --help
```

The project declares no runtime dependencies.

## Commands

### `resolve`

Resolve a DOI, PMID, PMCID, URL, arXiv ID, or title-like query into compact
metadata.

```bash
./paperutils resolve 10.1038/s41586-020-2649-2
./paperutils resolve PMID:32939066 --json
./paperutils resolve https://pubmed.ncbi.nlm.nih.gov/32939066/ --full-abstract
./paperutils resolve arXiv:1901.01234
./paperutils resolve https://www.biorxiv.org/content/10.1101/2019.12.31.892091v1.full.pdf
```

Biomedical resolution queries Crossref, Europe PMC, and PubMed E-utilities in
parallel. Any source may fail or time out independently. The command prints the
best merged result from sources that returned in time.

bioRxiv and medRxiv DOI/URL resolution also queries the official bioRxiv API.
When a version is available, `full_text_links` includes versioned preprint PDF
and landing page links.

Important field choices:

- `data_availability` is taken only from Europe PMC. If absent, it is printed as
  `Not found`.
- `abstract` prefers Europe PMC when available, otherwise PubMed or Crossref.
- `full_text_links` are collected from Europe PMC and Crossref.

### `accessions`

Resolve a paper, then extract dataset/database accessions from Europe PMC data
availability text and query GWAS Catalog by PMID.

```bash
./paperutils accessions 10.1038/s41586-020-2649-2
./paperutils accessions PMID:32939066 --json
```

Recognized accession families include GEO, SRA, ENA, BioProject, Assembly,
dbGaP, GWAS Catalog, and ArrayExpress.

### `lookup`

Lookup a single accession through ENA Portal API and NCBI E-utilities.

```bash
./paperutils lookup GSE100
./paperutils lookup PRJNA765432 --db bioproject
./paperutils lookup SRP111222 --db sra --json
```

The default `--db auto` mode chooses likely sources from the accession pattern.

### `search`

Search biomedical papers by title or keyword.

```bash
./paperutils search "alzheimer spatial transcriptomics" --limit 5
./paperutils search "array programming numpy" --json
```

Search currently uses Europe PMC first and Crossref as a fallback.

For CS/arXiv search:

```bash
./paperutils search "attention is all you need" --domain cs --limit 3
```

## Options

Common behavior:

- `--timeout SECONDS`: per-command API deadline, default `4.0`.
- `--json`: JSON output for agent or script consumers.
- `--domain auto|biomed|cs`: domain selector. `biomed` uses biomedical sources;
  `cs` uses arXiv.

## Tests

Offline tests use only local fixtures and standard-library `unittest`:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Optional live smoke tests hit public APIs and are disabled by default:

```bash
PAPERUTILS_LIVE_TESTS=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Live tests should be treated as smoke coverage only. They can fail because of
network issues, remote service downtime, or upstream data changes.

## Current Scope

Implemented:

- DOI, PMID, PMCID, URL, arXiv ID, and title-like identifier parsing.
- Biomedical `resolve` via Crossref, Europe PMC, and PubMed.
- CS/arXiv `resolve` and `search` via the arXiv Atom API.
- bioRxiv and medRxiv DOI/URL `resolve` via the official bioRxiv API.
- Dataset accession extraction from data availability text.
- GWAS Catalog study lookup by PMID.
- ENA and NCBI accession lookup.
- Text and JSON output.

Planned:

- Papers With Code and GitHub enrichment for CS papers.
- bioRxiv/medRxiv search beyond Europe PMC fallback.
- Better accession recall from Europe PMC cross references and full-text links.
- Download support for PDFs.
