# paperutils

`paperutils` is a dependency-free Python CLI that consolidates paper metadata
from multiple scholarly APIs into a single, structured dossier. It also
extracts and explains dataset accession numbers (GEO, SRA, BioProject, etc.)
from data availability statements.

Biomedical papers and arXiv/CS preprints are supported. No API keys are needed
— all sources are public.

## Installation

Python 3.10+ is required. The project has zero runtime dependencies.

**pip install:**

```bash
python3 -m pip install .
paperutils --help
```

**Run from source (no install):**

```bash
git clone https://github.com/vlln/paperutils.git
cd paperutils
./paperutils --help
```

The `./paperutils` launcher adds `src/` to `sys.path`, so no venv or pip step
is needed.

**Install as an agent skill:**

```bash
skit install github:vlln/paperutils --all
```

The [paperutils skill](https://github.com/vlln/paperutils/tree/master/skills/paperutils) ships with metadata and
usage rules so agents know when and how to call each command.

## Usage

```bash
# Search for papers by keyword or title
paperutils find "attention is all you need" --domain cs --limit 3
paperutils find "alzheimer spatial transcriptomics" --domain biomed

# Fetch a paper dossier by DOI, PMID, arXiv ID, URL, or title
paperutils get 10.1038/s41586-020-2649-2
paperutils get PMID:32939066 --json
paperutils get arXiv:1901.01234 --depth fast

# Explain a dataset accession
paperutils explain GSE100
paperutils explain PRJNA765432 --db bioproject
paperutils explain SRP111222 --db sra --json
```

### `find` — Search papers

Searches for papers by keyword or title. Returns ranked candidates; call `get`
on the best match to obtain the full dossier.

```bash
paperutils find <query> [--limit N] [--json] [--domain auto|biomed|cs]
```

| Flag | Effect |
|---|---|
| `--domain biomed` | Europe PMC + Crossref search. |
| `--domain cs` | arXiv Atom API. |
| `--domain auto` | (default) Chooses domain from query heuristics. |
| `--limit N` | Number of candidates (default 5). |

### `get` — Paper dossier

Assembles a structured dossier from Crossref, Europe PMC, PubMed, arXiv,
bioRxiv, and medRxiv. Accepts DOIs, PMIDs, PMCIDs, arXiv IDs, preprint URLs,
and free-text titles.

```bash
paperutils get <identifier> [--depth fast|full] [--json] [--full-abstract]
```

| Flag | Effect |
|---|---|
| `--depth fast` | Metadata, abstract, links, and extracted accessions (no verification). |
| `--depth full` | (default) Fast fields + GWAS Catalog lookup + per-accession ENA/NCBI expansion. |
| `--json` | JSON output instead of YAML-like text. |
| `--full-abstract` | Print full abstract without truncation. |

Output fields include: title, authors, journal/year, DOIs, PMID/PMCID, arXiv
ID, abstract, data availability statement, supplement links, code repositories,
dataset accessions, and full-text links.

### `explain` — Dataset accession lookup

Resolves an accession identifier to its metadata: title, source database,
sample count, and status.

```bash
paperutils explain <accession> [--db auto|geo|ena|sra|bioproject|assembly] [--json]
```

Powered by ENA Portal API and NCBI E-utilities. `--db auto` infers the source
from the accession prefix (e.g. `SRP` → SRA, `GSE` → GEO).

## Data Sources

### `find` — where search results come from

| Domain | API | Returns |
|---|---|---|
| `biomed` | [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search) | title, year, journal, DOI, PMID, PMCID |
| `biomed` | [Crossref](https://api.crossref.org/works) | title, year, journal, DOI |
| `cs` | [arXiv](https://export.arxiv.org/api/query) | title, year, DOI, arXiv ID |

Biomed queries Europe PMC and Crossref in parallel, then merges results
pairwise with duplicate detection (by DOI, falling back to title).

### `get` — where dossier fields come from

**Biomed papers** — up to 5 fetchers run in parallel via
`ThreadPoolExecutor`, each with a configurable timeout:

| Fetcher | API | Key fields |
|---|---|---|
| Crossref | [Crossref API](https://api.crossref.org/works) | title, authors, journal, year, DOI, abstract |
| Europe PMC | [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest) | abstract, data availability, PMID, PMCID, full-text links |
| PubMed | [NCBI E-utilities](https://eutils.ncbi.nlm.nih.gov/) | abstract, PMID, full-text links |
| bioRxiv | [bioRxiv API](https://api.biorxiv.org/details) | preprint version, JATS XML, bioRxiv PDF link |
| medRxiv | [medRxiv API](https://api.biorxiv.org/details) | preprint version, JATS XML, medRxiv PDF link |
| chemRxiv | [Crossref API](https://api.crossref.org/works) | preprint version, PDF link |

**CS papers** — 1 fetcher:

| Fetcher | API | Key fields |
|---|---|---|
| arXiv | [arXiv Atom API](https://export.arxiv.org/api/query) | title, authors, abstract, arXiv ID, DOI |

Fields are merged by precedence: sources with higher confidence overwrite
lower-confidence values. Europe PMC is authoritative for data availability
statements.

**`--depth full` enrichment** (additional APIs, one call per accession):

| Purpose | API | What it adds |
|---|---|---|
| Accession expansion | [ENA Portal API](https://www.ebi.ac.uk/ena/portal/api/) | study title, organism, submission date, status |
| Accession expansion | [NCBI E-utilities](https://eutils.ncbi.nlm.nih.gov/) | title, sample count, organism, submission date |
| GWAS Catalog | [GWAS Catalog REST API](https://www.ebi.ac.uk/gwas/rest/api) | GWAS study accessions linked to the PMID |
| Data repositories | [Zenodo](https://zenodo.org/api/) / [Figshare](https://api.figshare.com/) / [Dryad](https://datadryad.org/api/) / [OSF](https://api.osf.io/) | dataset metadata for direct resource URLs |

### `explain` — where accession metadata comes from

Accessions are classified by prefix (23 regex patterns), then looked up in
a sequence of candidates until one succeeds:

| API | Returns |
|---|---|
| [ENA Portal API](https://www.ebi.ac.uk/ena/portal/api/) (TSV) | title, organism, status, submission date |
| [NCBI E-utilities](https://eutils.ncbi.nlm.nih.gov/) (esearch + esummary) | title, sample count, organism, submission date |

## How It Works

### Architecture

```
                        ┌──────────────┐
                        │    cli.py    │
                        └──────┬───────┘
               ┌───────────────┼───────────────┐
          ┌────┴────┐   ┌─────┴─────┐   ┌──────┴──────┐
          │   get   │   │   find    │   │  explain    │
          └────┬────┘   └─────┬─────┘   └──────┬──────┘
               │              │                │
        ┌──────┴──────┐  ┌────┴────┐   ┌───────┴───────┐
        │  resolver   │  │ search  │   │  accessions   │
        └──────┬──────┘  └─────────┘   └───────────────┘
               │
    ┌──────────┼──────────┐
    │   fetchers package  │
    │  (one per source)   │
    │  arxiv    crossref  │
    │  biorxiv  chemrxiv  │
    │  pubmed   europepmc │
    └─────────────────────┘
```

### Get — Resolution pipeline

1. **Identify** — `identifiers.py` parses the input string and classifies it
   as a DOI, PMID, PMCID, arXiv ID, URL, or free-text title.
2. **Resolve** — `resolver.py` orchestrates calls to the relevant fetchers in
   parallel, each with a configurable timeout.
3. **Merge** — Results from multiple sources are merged into a single dossier.
   Fields are populated from the most authoritative source available.
4. **Enrich** — Accession numbers are extracted from the data availability
   statement via regex patterns. At `--depth full`, each accession is verified
   and expanded via `explain`. GWAS Catalog associations are looked up by PMID.
5. **Output** — `output.py` renders the dossier as YAML-like text or JSON.

### Find — Search pipeline

1. **Domain selection** — `--domain auto` uses query heuristics to choose
   between biomed and CS. Explicit `--domain biomed` or `--domain cs` bypasses
   detection.
2. **Query** — Biomed queries Europe PMC (REST API) and Crossref (title search)
   in parallel. CS queries the arXiv Atom API with `all:<query>` ranked by
   relevance.
3. **Merge** — Biomed results from Europe PMC and Crossref are interleaved
   pairwise, with duplicates removed by DOI (falling back to title). CS results
   from arXiv are returned as-is.
4. **Output** — Results are ranked and trimmed to `--limit` (default 5).
   `output.py` renders them as a table with year, PMID, DOI/arXiv ID, and title.

### Explain — Accession lookup pipeline

1. **Classify** — `accessions.py` matches the accession against 23 regex
   patterns covering GEO, SRA, ENA, BioProject, Assembly, dbGaP, GWAS,
   ArrayExpress, and CNGB prefixes (e.g. `GSE` → GEO, `SRP` → SRA, `PRJNA` →
   BioProject).
2. **Candidate selection** — Based on the classified type, a prioritized list
   of databases to try is built. `--db auto` infers this from the prefix;
   explicit `--db` overrides it.
3. **Lookup** — Each candidate is tried in order:
   - **ENA Portal API** — returns TSV with study title, organism, status, and
     submission date.
   - **NCBI E-utilities** — `esearch` resolves the accession to a UID, then
     `esummary` returns JSON metadata including title, sample count, organism,
     and submission date.
4. **Output** — The first successful lookup wins. `output.py` renders the
   result with accession, title, organism, type, samples, submitted date,
   status, and data source.

### Design decisions

**Why this exists.** `paperutils` is a CLI tool for AI agents. It does one thing:
collect structured metadata about a paper. It does not download PDFs, run batch
analyses, or generate plots — there are other tools for those jobs (e.g.
[paperscraper](https://github.com/jannisborn/paperscraper) for bulk literature
mining). The goal is to give an agent everything it needs to reason about a
single paper — identity, abstract, data/code availability, linked datasets,
supplement files — in a single command.

**Unix philosophy.** Each subcommand (`find`, `get`, `explain`) is an
independent tool that composes with others. `find` discovers candidates, `get`
resolves one into a dossier, `explain` expands an accession. Agents chain them:
search → pick best match → fetch dossier → verify datasets.

**Single-paper, not batch.** Every API call in the resolution pipeline is tied
to one identifier. There is no bulk dump, no local index, no queuing. This keeps
the tool simple, stateless, and predictable under the 4-second default timeout.

- **Zero dependencies** — only the Python standard library. This eliminates
  dependency conflicts and makes the tool trivially portable.
- **Tolerant of partial failures** — each API call has a default 4s timeout
  and failures are silently skipped. The best dossier from responding sources
  is always returned.
- **Public APIs only** — no API keys, tokens, or authentication required.
  All sources (Crossref, Europe PMC, PubMed, arXiv, NCBI E-utilities, ENA)
  are freely accessible.

## Limitations

- `download` (PDF/supplement retrieval) is planned but not yet implemented.
- CS enrichment (Papers With Code, GitHub metadata) is planned.
- `physics` domain under `find` is reserved but not yet connected to an API.
- Title-based `get` queries require the paper to exist in Europe PMC or
  Crossref search indices.

## License

MIT
