# Slide deck outline — data engineering trainer (this portfolio)

**Audience:** Trainers building PowerPoint / Google Slides / Marp.  
**Depth:** ~55 slides ≈ 1.5–2h talk + labs separate. Extend with screenshots from `dbt docs`, Delta folders, Streamlit.

**Full speaker notes (same slide order):** [TRAINER_SLIDES_WITH_SPEAKER_NOTES.md](TRAINER_SLIDES_WITH_SPEAKER_NOTES.md) · **Course marketing (10-day cohort):** [COURSE_MARKETING.md](COURSE_MARKETING.md)

**Convention:** Each block is one slide. Title = `# ...` line; bullets = talking points.

---

# Title slide

- Pakistani social protection — **data engineering portfolio** (synthetic)
- Trainer: [name] · Cohort: [date]
- Outcomes: run a **lakehouse-shaped** pipeline end-to-end (local open-source stack)

---

# What learners will build (picture)

- Files → **Bronze Delta** → **Silver Delta** → **dbt marts (DuckDB)** → **KPIs + dashboard**
- Same **shape** as Databricks/ADF production stacks

---

# Who this course is for

- **Beginners:** vocabulary + order of operations
- **Practitioners:** Spark + dbt integration patterns
- **Leads:** trade-offs + cloud migration narrative

---

# Ground rules (synthetic data)

- Numbers are **not** official statistics
- We teach **engineering patterns**: grain, lineage, tests, reruns

---

# Your machine (prereq checklist)

- Python **3.11**, JDK **11/17**, Git, 8 GB+ RAM
- Windows: PowerShell policy + `winutils` story (demo script)

---

# Repo map (tree mental model)

- `data_large/` · `ingest/` · `delta_lake/` · `notebooks/` · `dbt/` · `sql/` · `dashboard/` · `docs/`

---

# Medallion — Bronze

- “What **landed**” from upstream
- **Low opinion** transforms; preserve auditability

---

# Medallion — Silver

- **Conformed** entities: types, keys, dedupe
- Engineering disagreements **surface here**

---

# Medallion — Gold

- **Subject-area** tables / KPI grains
- Fewer joins for analysts / BI

---

# Why two engines here? (Spark + DuckDB)

- Spark: **lake-scale** writes + Delta
- DuckDB + dbt: **fast** modeling on a laptop

---

# Tool: Python & venv

- Isolation · reproducible pins (`requirements.txt`)
- **Avoid** wrong global Python (3.14 wheel gaps)

---

# Tool: PySpark (essentials)

- Driver + JVM even in `local[*]`
- **Lazy** transforms vs **actions**

---

# Tool: Delta Lake (essentials)

- `_delta_log` · ACID batch writes
- Path to **time travel** and schema evolution (concept)

---

# Tool: Jupyter / nbconvert

- **Interactive** exploration vs **headless** `nbconvert --execute`
- CI = same notebook, no UI

---

# Tool: dbt (the four moves)

- `source` · `ref` · **tests** · **docs**

---

# Tool: DuckDB

- In-process SQL analytics
- **`delta_scan`** bridges Silver paths into SQL

---

# Tool: Make & PowerShell scripts

- Same DAG, different shells
- Classroom parity on Windows

---

# Tool: pytest & Hypothesis

- Unit tests at **pure Python** boundary
- Properties = **invariants**

---

# Tool: Streamlit

- **Consumer** of marts — not a new truth layer
- Interactivity for stakeholder rehearsal

---

# Technique: grain (one row = …?)

- Every metric answer needs a **grain sentence**
- Tie to `data_dictionary.md`

---

# Technique: idempotency

- “What if this job runs **twice**?”
- Bronze overwrite vs merge (real world)

---

# Technique: data contracts

- dbt tests + documented columns
- Fail fast vs silent drift

---

# Technique: window functions (SQL + Spark)

- Rolling averages · rankings · running totals
- Appears in KPI SQL + marts

---

# Technique: file format trade-offs

- CSV.gz vs Parquet vs JSON vs Avro
- When schema hurts / helps

---

# Ingestion demo — single dataset

- `python ingest/ingest.py --dataset beneficiaries`
- Faster feedback loop in class

---

# Proof of Bronze

- Open `delta_lake/bronze/.../_delta_log`
- “This is a real Delta table, not CSV cosplay”

---

# Silver demo — theme: dedupe

- Why duplicates exist (retries, upstream bugs)
- Show before/after row counts (conceptual)

---

# Silver demo — theme: windows

- Ranking / partitions tied to business questions

---

# Environment variable — `DELTA_LAKE_PATH`

- dbt **parse-time** requirement
- Forward slashes on Windows

---

# dbt staging (`stg_*`)

- 1:1 with Silver sources
- Rename + cast discipline

---

# dbt intermediate (`int_*`)

- Reusable joins / bridges
- DRY for multiple marts

---

# dbt marts (`mart_*`)

- KPI-ready grains
- Materialized as **tables** here

---

# dbt docs & lineage (screenshot slide)

- “This is your **communication** artifact with analysts”

---

# dbt tests (types)

- Schema tests vs singular SQL tests
- Where to enforce business rules

---

# KPI SQL — why standalone files?

- Analyst-ready **recipes**
- Portable to BI tools / Databricks SQL

---

# Dashboard — reading the storyboard

- Heatmaps = **patterns**
- Ranked bars = **snapshots**
- Volume + rate = **anti-ambiguity**

---

# Operations — runbooks

- Ingestion runbook · dbt runbook
- Day-2 on-call mindset (local simulation)

---

# Clean & retry

- `make clean` / `clean-artifacts.ps1`
- Windows file handles + Spark shutdown

---

# Cloud mapping — ingest

- `ingest.py` ↔ ADF-triggered **Databricks** job

---

# Cloud mapping — storage

- Local Delta paths ↔ **ADLS Gen2** + Unity Catalog

---

# Cloud mapping — dbt

- `dbt-duckdb` ↔ **`dbt-databricks`**
- Adapter swap + catalog paths

---

# Cloud mapping — orchestration

- `make all` ↔ **Databricks Workflows** / ADF pipeline

---

# Security & PII (discussion slide)

- Synthetic data avoids privacy incidents
- Production: masking, row access policies, audit logs

---

# Performance (concept only)

- Shuffle cost · partition pruning
- “Not optimising premature — **measuring** first”

---

# Formative check — exit ticket

- “What breaks if Silver is missing?”

---

# Summative lab — preview

- Add a test **or** document a mart grain in YAML

---

# Rubric (high level)

- Correctness · grain · lineage hygiene · communication

---

# Mock interview Q1

- Walk file → KPI on a dashboard (60 seconds)

---

# Mock interview Q2

- Where do you test: Python vs dbt vs integration?

---

# Mock interview Q3

- Migrate this repo to Databricks — what changes first?

---

# Stretch topics (if time)

- Incremental models · SCD2 · streaming ingestion
- Unity Catalog governance patterns

---

# Homework pack (optional)

- Read `CONCEPTS_AND_PURPOSE.md`
- Run one stage with intentional failure + fix write-up

---

# Q&A + next steps

- Point to `docs/training/COMPLETE_TECHNICAL_TRAINER_GUIDE.md`
- Thank you / office hours

---

## Optional appendix slides (duplicate as needed)

- Screenshot: `pytest` green  
- Screenshot: Streamlit heatmap  
- Screenshot: `dbt test` failure example  
- Diagram: README Mermaid architecture (export PNG)

---

*Deck outline ends. Speaker notes: [TRAINER_SLIDES_WITH_SPEAKER_NOTES.md](TRAINER_SLIDES_WITH_SPEAKER_NOTES.md). Deep technical notes: [COMPLETE_TECHNICAL_TRAINER_GUIDE.md](COMPLETE_TECHNICAL_TRAINER_GUIDE.md).*
