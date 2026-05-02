写一个Python程序, 具有CLI脚本外观(paperutils). 功能:
  paperutils resolve <identifier>       # 解析一篇论文的所有可用元数据
  paperutils accessions <identifier>    # 查找论文关联的数据库 accession / 数据集
  paperutils lookup <accession>         # 查询单个 accession 的详情
  paperutils search <query>             # 按标题/关键词搜索论文（返回候选列表）
 
### 子命令设计细节

#### 1. `paperutils resolve <identifier>`

**输入**：DOI、PMID、PMCID、或 URL（自动解析出 ID）  
**内部逻辑**：并发查询 Crossref + Europe PMC + PubMed E-utilities，合并去重  
**输出格式**：精简的 YAML 或 key-value（Agent 容易读）

```
# paperutils resolve 10.1038/s41586-023-05564-0

title: "A spatially resolved brain atlas of gene expression in Alzheimer's disease"
authors: Smith J, Doe K, et al. (10 authors)
journal: Nature
year: 2023
doi: 10.1038/s41586-023-05564-0
pmid: 36653456
pmcid: PMC9876543
abstract: "Alzheimer's disease is characterized by... (truncated at 500 chars)"
data_availability: "Raw sequencing data are available at GEO under GSE123456. Code is at https://github.com/..."
sources: crossref, europepmc, pubmed
```

`data_availability` 是关键 —— Europe PMC 专门有 `dataAvailability` 字段，你要重点提取。如果没有，就写 `"Not found"`。

---

#### 2. `paperutils accessions <identifier>`

**输入**：同 resolve（DOI / PMID / PMCID）  
**内部逻辑**：从 Europe PMC 的 data availability 文本中正则提取 accession（GSE、SRP、PRJNA、GCA 等），同时查询 GWAS Catalog API。  
**输出**：简洁的列表，每行一个

```
# paperutils accessions PMID:36653456

type       accession     description
GEO        GSE123456      RNA-seq of Alzheimer's brain
GWAS       GCST001234     Alzheimer's disease GWAS
ENA        PRJEB54321     matching study in ENA
```

这个工具让 Agent 拿到论文后，直接知道“有哪些数据集可以碰”。

---

#### 3. `paperutils lookup <accession>`

**输入**：GEO accession、ENA accession、SRP、BioProject 等  
**内部逻辑**：调 ENA Portal API / NCBI E-utilities（esearch + efetch）拿到基础信息  

```
# paperutils lookup GSE123456

accession:   GSE123456
title:       RNA-seq of Alzheimer's disease brain samples
organism:    Homo sapiens
type:        Expression profiling by high throughput sequencing
samples:     120
submitted:   2023-05-12
status:      Public
```

### 内部的容错与并发

每个 `resolve` 调用内部要做：

1. 同时请求 Crossref API、Europe PMC API、PubMed E-utilities
2. 只要有一个响应成功就开始组装结果（不等待全部）
3. 元数据字段按可靠性排序选用：data availability 只用 Europe PMC，摘要优先 Europe PMC 次选 PubMed，题录可以相互补全
4. 4 秒超时（API 必须快，否则不适合 CLI）(可配置)

这样设计的好处：
- 调用 `paperutils resolve` 就**一次性获得全部可用元数据**
- 不需要知道背后有 3 个 API
- 输出量是一页终端以内，Agent 上下文窗口友好
- `accessions` 子命令解决了“复现 Agent 最需要的数据可达性”问题

  paperutils resolve <identifier>
  自动识别规则：
 
  标识符模式识别为查询策略
  10.xxx/xxxDOICrossref + Europe PMC + PubMed 三并发
  PMID:32405050 或纯数字 8 位PMIDEurope PMC + PubMed
  PMCID:PMC9876543 或 PMC9876543PMCIDEurope PMC + PubMed
  arXiv:1901.01234arXiv ID（可选扩展）
  以 http 开头URL先提取 DOI/PMID，再按上述规则
  其他当作标题搜索走 search 流程
 

 resolve 输出里有 full_text_links 字段, 提供下载链接
full_text_links:
  - pmc: http://www.ncbi.nlm.nih.gov/pmc/articles/PMC9876543/pdf/
  - publisher: https://www.nature.com/articles/s41586-023-05564-0.pdf
  - preprint: https://arxiv.org/pdf/1901.01234
  - ...
 
设计上应该预留多领域空间。

按领域分类看数据源
领域	需要的数据源	当前覆盖
生物医学	PubMed, Europe PMC, GWAS Catalog, ENA, GEO	✅ 核心覆盖
计算机 / AI	arXiv, DBLP, Papers With Code, GitHub	❌ 未覆盖
物理/数学	arXiv, INSPIRE, ADS	❌ 未覆盖
化学	PubChem, ChemRxiv	❌ 未覆盖
社会科学	SSRN, RePEc	❌ 未覆盖

paperutils resolve 10.1038/xxx           # 自动走生物医学源
paperutils resolve arXiv:1901.01234       # 自动走 arXiv + CS 源
paperutils resolve --domain cs 1901.01234 # 明确指定领域（可选）

#### 内部架构
第一版只做生物医学，但设计接口时让后续新增领域只需注册新 fetcher：
FETCHERS = {
    "biomed": [CrossrefFetcher, EuropePMCFetcher, PubmedFetcher, GWASFetcher],
    "cs":     [ArxivFetcher, SemanticScholarFetcher, PapersWithCodeFetcher],
    "physics": [ArxivFetcher, ADSfetcher, INSPIREFetcher],
}
 

```
paperutils <subcommand> [arguments] [options]

子命令：
  resolve <identifier>      解析论文元数据（DOI/PMID/PMCID/arXiv/URL）
  accessions <identifier>   列出关联数据集 accession
  lookup <accession>        查询 accession 详情
  search <query>            搜索论文
  download <identifier>     下载 PDF（Phase 2）

resolve 参数：
  <identifier>             必填，支持 DOI/PMID/PMCID/arXiv/URL/标题
  --json                   输出 JSON 格式（默认人类可读文本）
  --full-abstract          不截断摘要
  --domain auto|biomed|cs  手动指定领域（默认 auto 自动推断）

accessions 参数：
  <identifier>             同 resolve
  --json                   输出 JSON

lookup 参数：
  <accession>              GEO/SRA/ENA accession
  --json                   输出 JSON
  --db auto|geo|ena|sra   指定数据库（默认 auto）

search 参数：
  <query>                  标题或关键词
  --limit 5                返回数量（默认 5）
  --domain auto|biomed|cs  搜索范围
```


# 代码规范:
Google规范, 良好的解耦合, 但不过度设计.

