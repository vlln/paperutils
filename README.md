# paperutils

`paperutils` is a dependency-free Python CLI for paper discovery, paper dossiers,
and dataset/accession explanation. It currently focuses on biomedical papers and
arXiv/CS preprints, using only the Python standard library.

## Commands

`paperutils` exposes three core commands:

```bash
./paperutils get <identifier>
./paperutils find <query>
./paperutils explain <accession>
```

There are no legacy aliases. Older command names such as `resolve`,
`accessions`, `lookup`, and `search` are intentionally not supported.

## `get`

Get a complete paper dossier from a DOI, PMID, PMCID, arXiv ID, URL, preprint
DOI, or title.

```bash
./paperutils get 10.1038/s41586-020-2649-2
./paperutils get PMID:32939066 --json
./paperutils get arXiv:1901.01234
./paperutils get https://www.biorxiv.org/content/10.1101/2019.12.31.892091v1.full.pdf
```

Output is structured as:

```yaml
identity:
  title: ...
  authors: ...
  journal: ...
  year: ...
  doi: ...
  pmid: ...
  pmcid: ...
  arxiv_id: ...
  preprint_server: ...
  preprint_version: ...
abstract: ...
data_availability: ...
supplement:
  pdf: ...
  files: []
code_repos: []
datasets:
  - accession: ...
    type: ...
    title: ...
    samples: ...
    status: ...
full_text_links:
  - type: publisher
    url: ...
sources:
  - europepmc
  - crossref
```

Depth controls how much work `get` does:

```bash
./paperutils get <identifier> --depth fast
./paperutils get <identifier> --depth full
```

- `fast`: metadata, abstract, data availability, full text links, and extracted
  dataset accessions. It does not verify dataset details.
- `full`: all fast fields, plus GWAS Catalog lookup and per-accession
  `explain` expansion where possible.

`get` queries Crossref, Europe PMC, PubMed, arXiv, bioRxiv, and medRxiv as
appropriate. It tolerates partial API failures and returns the best dossier from
sources that respond in time.

## `find`

Find candidate papers by title or keyword.

```bash
./paperutils find "array programming numpy" --limit 3
./paperutils find "attention is all you need" --domain cs --limit 3
./paperutils find "alzheimer spatial transcriptomics" --domain biomed
```

Options:

- `--domain auto|biomed|cs|physics`: `biomed` uses Europe PMC/Crossref; `cs`
  uses arXiv. `physics` is reserved and currently not implemented.
- `--limit N`: number of candidates, default `5`.
- `--json`: JSON output.

Agents should use `find` when the exact DOI/PMID/arXiv ID is not known, then
call `get` on the chosen candidate.

## `explain`

Explain one dataset/accession identifier.

```bash
./paperutils explain GSE100
./paperutils explain PRJNA765432 --db bioproject
./paperutils explain SRP111222 --db sra --json
```

Supported sources currently include ENA Portal API and NCBI E-utilities. The
default `--db auto` mode chooses likely sources from the accession pattern.

## Run From Source

```bash
./paperutils --help
./paperutils get 10.1038/s41586-020-2649-2
./paperutils find "numpy array programming" --limit 3
./paperutils explain GSE100
```

The source checkout runner adds `src/` to `sys.path`, so no installation step is
required.

## Install Locally

```bash
python3 -m pip install .
paperutils --help
```

The project declares no runtime dependencies.

## Tests

Offline tests use only local fixtures and standard-library `unittest`:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Optional live smoke tests hit public APIs and are disabled by default:

```bash
PAPERUTILS_LIVE_TESTS=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Live tests are smoke coverage only. They can fail because of network issues,
remote service downtime, or upstream data changes.

## Current Scope

Implemented:

- DOI, PMID, PMCID, URL, arXiv ID, and title-like identifier parsing.
- One-stop `get` dossier assembly.
- Biomedical metadata via Crossref, Europe PMC, PubMed, bioRxiv, and medRxiv.
- CS/arXiv metadata and search via the arXiv Atom API.
- Supplementary file classification from Crossref and Europe PMC links.
- Dataset accession extraction from data availability text.
- GitHub, Zenodo, Figshare, Dryad, and OSF extraction from data availability text.
- GWAS Catalog lookup by PMID during `get --depth full`.
- ENA and NCBI accession explanation.
- Text and JSON output.

Planned:

- `download` for PDFs and supplement files.
- Papers With Code and GitHub enrichment for CS papers.
- Zenodo/Figshare metadata and dataset DOI explanation.
- Better accession recall from Europe PMC cross references and full-text links.
