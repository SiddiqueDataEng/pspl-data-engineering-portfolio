# Trainer slides — speaker notes manuscript

**Purpose:** One slide per block, `---` separators — paste into **Marp**, **Google Slides**, or PowerPoint.  
**Compact outline only:** [SLIDE_DECK_OUTLINE.md](SLIDE_DECK_OUTLINE.md) · **Labs and demos:** [COMPLETE_TECHNICAL_TRAINER_GUIDE.md](COMPLETE_TECHNICAL_TRAINER_GUIDE.md) (especially §14) · **Marketing / 10‑day map:** [COURSE_MARKETING.md](COURSE_MARKETING.md)

**Convention:** `## Slide NN` = advance; **On slide** = visible bullets; **Speaker notes** = narration + demo cues.

---

## Slide 01 — Title slide

**On slide:**

- Pakistani social protection — **data engineering portfolio** (synthetic)
- Trainer: [name] · Cohort: [date]
- Outcomes: run a **lakehouse-shaped** pipeline end-to-end (local open-source stack)

**Speaker notes:**

Welcome people and set expectations: this is a **skills portfolio**, not a policy statistics course. In one sentence, we will land files into **Delta**, clean in **Spark**, model in **dbt**, and read marts in **SQL and Streamlit** — all locally. Mention that **numbers are fictional** but **patterns are real** (grain, tests, lineage). Optionally show the repo root in the IDE for five seconds so the room sees it is a real codebase.

---

## Slide 02 — What learners will build (picture)

**On slide:**

- Files → **Bronze Delta** → **Silver Delta** → **dbt marts (DuckDB)** → **KPIs + dashboard**
- Same **shape** as Databricks/ADF production stacks

**Speaker notes:**

This slide is the **north star**. Transition from the title by saying “here is the picture you should hold in your head for ten days.” Emphasize **order**: nothing in Gold makes sense if Silver contracts are wrong. Name-check **ADF** and **Databricks** as the *cloud analogue* without opening a cloud console yet — you are promising **conceptual isomorphism**, not identical SKUs.

---

## Slide 03 — Who this course is for

**On slide:**

- **Beginners:** vocabulary + order of operations
- **Practitioners:** Spark + dbt integration patterns
- **Leads:** trade-offs + cloud migration narrative

**Speaker notes:**

Acknowledge mixed rooms. Beginners get permission to focus on **order and verification**; practitioners should zoom into **`delta_scan`**, dbt **DAG**, and **tests**; leads should listen for **idempotency, contracts, and migration**. Invite people to self‑identify mentally — you will reuse these personas when assigning homework difficulty.

---

## Slide 04 — Ground rules (synthetic data)

**On slide:**

- Numbers are **not** official statistics
- We teach **engineering patterns**: grain, lineage, tests, reruns

**Speaker notes:**

Say this clearly to avoid **misuse of synthetic humanitarian-style data** in external reports. Pivot quickly to **why** synthetic is an advantage in class: we can break pipelines and inject duplicates without ethical incidents. Tie “patterns” to the **rubric** later (correctness, grain, lineage hygiene, communication).

---

## Slide 05 — Your machine (prereq checklist)

**On slide:**

- Python **3.11**, JDK **11/17**, Git, 8 GB+ RAM
- Windows: PowerShell policy + `winutils` story (demo script)

**Speaker notes:**

Be firm about **Python 3.11**: wrong Python versions cause wheel builds and wasted class time. Demo `java -version` and, on Windows, mention **`run-full-pipeline.ps1`** as the blessed path that sets **HADOOP_HOME** / `winutils` patterns. Point learners to [LEARNING_GUIDE.md](../LEARNING_GUIDE.md) for screenshots-level detail — do not troubleshoot every OS from this slide.

---

## Slide 06 — Repo map (tree mental model)

**On slide:**

- `data_large/` · `ingest/` · `delta_lake/` · `notebooks/` · `dbt/` · `sql/` · `dashboard/` · `docs/`

**Speaker notes:**

Use the trainer line: **“Artifacts, not slides, are the curriculum.”** Trace with the laser pointer or cursor: **inputs** live under `data_large/`; **code** in `ingest/` and `notebooks/`; **lake output** under `delta_lake/`; **warehouse models** in `dbt/`; **consumer SQL** in `sql/`; **dashboard** in `dashboard/`; **truth about meaning** in `docs/` and `data_dictionary.md`. Ask learners to sketch the same tree on paper — **Session S1** check.

---

## Slide 07 — Medallion — Bronze

**On slide:**

- “What **landed**” from upstream
- **Low opinion** transforms; preserve auditability

**Speaker notes:**

Bronze is **not** “bad data” — it is **faithful capture**. Minimal opinion preserves **replay** and audit stories. In this repo, Bronze is written by **`ingest.py`** into **Delta** under `delta_lake/bronze/`. Contrast with a naive CSV dump: Delta gives **table semantics** and a transaction log learners can open.

---

## Slide 08 — Medallion — Silver

**On slide:**

- **Conformed** entities: types, keys, dedupe
- Engineering disagreements **surface here**

**Speaker notes:**

Silver is where teams argue **dedupe keys**, **null handling**, and **grain** — that is healthy. Here Silver is produced in **`notebooks/delta_lake_operations.ipynb`**. Position the notebook as “**heavy row Spark** still common in enterprises,” not as a rejection of dbt.

---

## Slide 09 — Medallion — Gold

**On slide:**

- **Subject-area** tables / KPI grains
- Fewer joins for analysts / BI

**Speaker notes:**

Gold answers “**what does the business read weekly?**” In this repo, Gold is **dbt marts** materialized into **DuckDB**. Stress **documented grain** — every mart should have a **one row means …** sentence; point to `data_dictionary.md` as homework support.

---

## Slide 10 — Why two engines here? (Spark + DuckDB)

**On slide:**

- Spark: **lake-scale** writes + Delta
- DuckDB + dbt: **fast** modeling on a laptop

**Speaker notes:**

This is the **architecture decision** slide. Spark owns **lake writes** and messy row logic; DuckDB + dbt own **cheap, fast warehouse modeling** on a laptop. The bridge is **`delta_scan`** reading Silver paths — **logically** still downstream of the lake. Preview: in production you might collapse engines, but **separation of concerns** remains interview gold.

---

## Slide 11 — Tool: Python & venv

**On slide:**

- Isolation · reproducible pins (`requirements.txt`)
- **Avoid** wrong global Python (3.14 wheel gaps)

**Speaker notes:**

Teach **`python -m venv .venv`** (or `setup.ps1` on Windows) as a **professional habit**, not ceremony. Show `pip show dbt-core` from the venv. If someone is on Python 3.14, **stop** and fix early — reference troubleshooting table in the trainer guide §16.

---

## Slide 12 — Tool: PySpark (essentials)

**On slide:**

- Driver + JVM even in `local[*]`
- **Lazy** transforms vs **actions**

**Speaker notes:**

Even **local** Spark is a **JVM story** — hence Java prereq. Draw the mental model: **transformations** build a plan; **`count`**, **`write`**, **`show`** are **actions** that execute. Mention **shuffle** only as “expensive joins/groupBy — we will not optimise prematurely; we will **measure** when needed.”

---

## Slide 13 — Tool: Delta Lake (essentials)

**On slide:**

- `_delta_log` · ACID batch writes
- Path to **time travel** and schema evolution (concept)

**Speaker notes:**

Open a Bronze folder in the file explorer or IDE and point at **`_delta_log`** — this is the “**not CSV cosplay**” moment. ACID batch writes are why Bronze/Silver behave like **tables**. Time travel and evolution are **production talking points** even if the notebook only demos one read pattern.

---

## Slide 14 — Tool: Jupyter / nbconvert

**On slide:**

- **Interactive** exploration vs **headless** `nbconvert --execute`
- CI = same notebook, no UI

**Speaker notes:**

Position notebooks as **two modes**: human exploration vs **automation**. **`jupyter nbconvert --execute`** is the bridge to **CI / scheduled jobs** — same artifact, no browser. This sets up later **orchestration** thinking (`make all` as a DAG).

---

## Slide 15 — Tool: dbt (the four moves)

**On slide:**

- `source` · `ref` · **tests** · **docs**

**Speaker notes:**

dbt is **versioned analytics engineering**. The four moves are the **minimum vocabulary**: **`source`** declares external truth; **`ref`** builds an explicit DAG; **tests** encode contracts; **docs** communicate with analysts. Promise **`dbt docs`** as a stakeholder artifact they will screenshot for portfolios.

---

## Slide 16 — Tool: DuckDB

**On slide:**

- In-process SQL analytics
- **`delta_scan`** bridges Silver paths into SQL

**Speaker notes:**

DuckDB is **in-process** — the database file is **`pspl.duckdb`** per `profiles.yml`. **`delta_scan`** is the **magic bridge**: SQL over **Delta files** on disk without running Spark for every Gold query. This is the **technical heart** of the two-engine pattern.

---

## Slide 17 — Tool: Make & PowerShell scripts

**On slide:**

- Same DAG, different shells
- Classroom parity on Windows

**Speaker notes:**

**`Makefile`** vs **`scripts/*.ps1`** is **inclusive tooling** — same stages, different shells. In mixed classrooms, **do not** shame Windows users; praise the scripts that set **`DELTA_LAKE_PATH`**, **HADOOP_HOME**, and ordering. Demo listing targets: `make help` or open `run-full-pipeline.ps1` header comments.

---

## Slide 18 — Tool: pytest & Hypothesis

**On slide:**

- Unit tests at **pure Python** boundary
- Properties = **invariants**

**Speaker notes:**

Tests **buy the right to refactor**. Python tests shine on **pure transforms** (`transforms.py`). Hypothesis is optional depth: **properties** express invariants (bounds, monotonicity). Contrast with **dbt tests** on relational contracts — different layer, same discipline.

---

## Slide 19 — Tool: Streamlit

**On slide:**

- **Consumer** of marts — not a new truth layer
- Interactivity for stakeholder rehearsal

**Speaker notes:**

Streamlit reads **marts** — it must **not** invent new business rules. Use it as **“analyst experience rehearsal”**: filters, coordinated charts, heatmaps vs bars. Tie to **Session S5** in the trainer guide: learners write **grain + business question** for one KPI.

---

## Slide 20 — Technique: grain (one row = …?)

**On slide:**

- Every metric answer needs a **grain sentence**
- Tie to `data_dictionary.md`

**Speaker notes:**

Make the room say grain out loud once. Example pattern: “**One row per beneficiary per month**.” If grain is wrong, **every dashboard is lies**. Assign **`data_dictionary.md`** as the analyst contract reference. This slide supports both **SQL KPIs** and **marts**.

---

## Slide 21 — Technique: idempotency

**On slide:**

- “What if this job runs **twice**?”
- Bronze overwrite vs merge (real world)

**Speaker notes:**

Idempotency is a **production mindset** question. In this demo ingest may **overwrite** Bronze — discuss **merge semantics** and ** Slowly Changing Dimensions** as **where teams graduate** after the camp. Ask for a show of hands: “who has rerun a job because the cluster died?” — relate emotionally.

---

## Slide 22 — Technique: data contracts

**On slide:**

- dbt tests + documented columns
- Fail fast vs silent drift

**Speaker notes:**

Contracts are **tests + descriptions + agreed grain**. **Fail fast** (`dbt test` red) beats silent dashboard drift. Bridge to **Delta schema evolution** as a production adjacent topic — contracts evolve, they are not static.

---

## Slide 23 — Technique: window functions (SQL + Spark)

**On slide:**

- Rolling averages · rankings · running totals
- Appears in KPI SQL + marts

**Speaker notes:**

Windows appear in **both** Spark Silver work and **`sql/`** KPI files — unify the pedagogy: **partition** and **order** frame the business question. Promise one **`ROWS BETWEEN`** example later when live in SQL or notebook.

---

## Slide 24 — Technique: file format trade-offs

**On slide:**

- CSV.gz vs Parquet vs JSON vs Avro
- When schema hurts / helps

**Speaker notes:**

Walk the **`ingest/readers.py`** table mentally: each format teaches a **different failure mode** (compression, nested JSON, Avro schema). This supports **interview stories** about ingestion design — not just tool trivia.

---

## Slide 25 — Ingestion demo — single dataset

**On slide:**

- `python ingest/ingest.py --dataset beneficiaries`
- Faster feedback loop in class

**Speaker notes:**

**Say:** “Bronze answers: what landed?” **Show:** run **`python ingest/ingest.py --dataset beneficiaries`** (or Windows `py -3.11` equivalent). **Do:** learners pick a second dataset flag. **Check:** Bronze folder exists — **Session S2** script. Keep Spark runtime tolerable by **subsetting**.

---

## Slide 26 — Proof of Bronze

**On slide:**

- Open `delta_lake/bronze/.../_delta_log`
- “This is a real Delta table, not CSV cosplay”

**Speaker notes:**

Physical proof beats slides. Open **`_delta_log`** in the editor or list dir in terminal. Narrate: **transaction log entries** mean **ACID** semantics and **replay** stories. This slide is intentionally **short** — let the filesystem be the star.

---

## Slide 27 — Silver demo — theme: dedupe

**On slide:**

- Why duplicates exist (retries, upstream bugs)
- Show before/after row counts (conceptual)

**Speaker notes:**

**Say:** “Silver is where engineering disagreements surface.” **Show:** notebook cells: read Bronze → **dedupe** → write Silver — do not rush the whole notebook if timeboxed. **Check:** learner articulates **why duplicates happen** (retries, idempotent upstream failures). Row counts before/after are optional if demo data is stable.

---

## Slide 28 — Silver demo — theme: windows

**On slide:**

- Ranking / partitions tied to business questions

**Speaker notes:**

Pick **one** window example tied to a **realistic question** (e.g. ranking payments or complaints). Emphasize **partition keys** reflect **business dimensions** — wrong partition, wrong ranking. Link forward to **KPI SQL** that reuses similar logic.

---

## Slide 29 — Environment variable — `DELTA_LAKE_PATH`

**On slide:**

- dbt **parse-time** requirement
- Forward slashes on Windows

**Speaker notes:**

This variable breaks classes if skipped — lean into it. **`sources.yml`** embeds **`env_var('DELTA_LAKE_PATH')`** so dbt **parses** paths to Silver. **Show** the error when unset, then fix via **export** (Unix) or **pipeline script** (Windows). Stress **forward slashes** even on Windows.

---

## Slide 30 — dbt staging (`stg_*`)

**On slide:**

- 1:1 with Silver sources
- Rename + cast discipline

**Speaker notes:**

Staging is the **adapter layer** — thin, boring, reliable. **`stg_*`** should be **1:1** with Silver tables with **casts and renames** only; **no business joins** here. Demo `dbt run --select stg_beneficiaries+` as a **subgraph** debugging habit.

---

## Slide 31 — dbt intermediate (`int_*`)

**On slide:**

- Reusable joins / bridges
- DRY for multiple marts

**Speaker notes:**

**`int_*`** is where **DRY** happens — reusable joins and bridges consumed by **multiple marts**. Warn against **“god models”** that mix unrelated subject areas — intermediates should still read as **coherent building blocks**.

---

## Slide 32 — dbt marts (`mart_*`)

**On slide:**

- KPI-ready grains
- Materialized as **tables** here

**Speaker notes:**

**`mart_*`** is analyst‑facing: **KPI-ready grain**, fewer joins at consumption time. In this project marts materialize as **tables in DuckDB** for speed — note this is a **pedagogical choice**, not a universal law. Ask for a **grain sentence** for one displayed mart.

---

## Slide 33 — dbt docs & lineage (screenshot slide)

**On slide:**

- “This is your **communication** artifact with analysts”

**Speaker notes:**

Run **`dbt docs generate && dbt docs serve`** (or show a prepared screenshot if offline). Slow down: **lineage graph edges** are the **contract visualization**. Assign portfolio capture: **one lineage screenshot** annotated with their own words in the capstone.

---

## Slide 34 — dbt tests (types)

**On slide:**

- Schema tests vs singular SQL tests
- Where to enforce business rules

**Speaker notes:**

**Schema tests** in YAML are fast to standardize; **singular tests** encode **weird one-offs** and cross‑table rules. Business rules belong where **analysts and engineers agree** — usually **dbt** for relational contracts, **Python** for pure transforms. Tease **summative**: add a test on a rate column between 0 and 1.

---

## Slide 35 — KPI SQL — why standalone files?

**On slide:**

- Analyst-ready **recipes**
- Portable to BI tools / Databricks SQL

**Speaker notes:**

**`sql/`** proves marts are **not** trapped in one dashboard — they are **reusable**. Each file is a **teachable module**: CTEs, joins, windows. Mention **`scripts/run-sql-kpis.ps1`** for Windows parity. Bridge: these files port to **Databricks SQL** with connection swaps.

---

## Slide 36 — Dashboard — reading the storyboard

**On slide:**

- Heatmaps = **patterns**
- Ranked bars = **snapshots**
- Volume + rate = **anti-ambiguity**

**Speaker notes:**

Teach **how to read** charts, not just how to build them. Heatmaps show **spatial/temporal structure**; ranked bars show **snapshots**; pairing **volume + rate** avoids **base-rate fallacies**. Open Streamlit if runtime allows — else static screenshot.

---

## Slide 37 — Operations — runbooks

**On slide:**

- Ingestion runbook · dbt runbook
- Day-2 on-call mindset (local simulation)

**Speaker notes:**

Assign **`docs/runbooks/`** as **day‑2 ops** reading. Runbooks are **how you reduce tribal knowledge**. Contrast local **`print`** logging with **driver logs / metrics** in cloud — same **operational questions**, different sinks.

---

## Slide 38 — Clean & retry

**On slide:**

- `make clean` / `clean-artifacts.ps1`
- Windows file handles + Spark shutdown

**Speaker notes:**

**Clean** is a **pedagogical superpower** — resets bad partial states. On Windows, **file locks** between Spark and DuckDB are real; scripts often **sleep** or enforce order — explain **why** so learners do not assume flakiness is “random.”

---

## Slide 39 — Cloud mapping — ingest

**On slide:**

- `ingest.py` ↔ ADF-triggered **Databricks** job

**Speaker notes:**

First row of the **local → cloud** table. **`ingest.py`** is the **batch land** step; in cloud, **ADF** (or equivalent) **triggers** a **Databricks job** with parameters and retries. Emphasize **orchestration metadata** (SLAs, retries) as the new complexity — not the pandas/Spark line itself.

---

## Slide 40 — Cloud mapping — storage

**On slide:**

- Local Delta paths ↔ **ADLS Gen2** + Unity Catalog

**Speaker notes:**

Paths become **`abfss://`** URIs; governance moves to **Unity Catalog** rules. Learners keep the **mental map**: same **Delta log abstraction**, different **security perimeter**.

---

## Slide 41 — Cloud mapping — dbt

**On slide:**

- `dbt-duckdb` ↔ **`dbt-databricks`**
- Adapter swap + catalog paths

**Speaker notes:**

**dbt** is the **stable skill** — adapters change. Teaching points: **`profiles.yml`**, **`dbt-databricks`**, **catalog** paths, **warehouse** endpoints. This is the **confidence slide** for analytics engineers.

---

## Slide 42 — Cloud mapping — orchestration

**On slide:**

- `make all` ↔ **Databricks Workflows** / ADF pipeline

**Speaker notes:**

**`make all`** is a **DAG** with ordering; cloud equivalents add **retry policies**, **alerts**, and **backfills**. Invite learners to narrate **one failure** (e.g. Silver missing) and what **orchestrator** behavior they would want.

---

## Slide 43 — Security & PII (discussion slide)

**On slide:**

- Synthetic data avoids privacy incidents
- Production: masking, row access policies, audit logs

**Speaker notes:**

Synthetic data is an **ethical feature** for training. Production adds **masking**, **row-level security**, **audit logs**, and **access reviews** — no hands‑on here, but **interview credibility** requires naming these controls.

---

## Slide 44 — Performance (concept only)

**On slide:**

- Shuffle cost · partition pruning
- “Not optimising premature — **measuring** first”

**Speaker notes:**

Avoid **premature optimisation lectures** — instead teach **measurement posture**: **shuffle** is the usual villain; **partition pruning** is the hero in big data stories. Relate only at **concept** level unless profiling is a stretch goal.

---

## Slide 45 — Formative check — exit ticket

**On slide:**

- “What breaks if Silver is missing?”

**Speaker notes:**

Pause for **60–90 seconds** writing. Expected answer path: **dbt `delta_scan`** paths fail or return empty; **Gold** is wrong or absent; **dashboard** lies or errors. Collect 2–3 answers aloud — **normalize struggle**.

---

## Slide 46 — Summative lab — preview

**On slide:**

- Add a test **or** document a mart grain in YAML

**Speaker notes:**

Set up **Session summative** per guide §15.2: **schema test** (e.g. rate between 0 and 1) **or** new column in staging with **description** + test. Show the **rubric** next slide as the **grading contract**.

---

## Slide 47 — Rubric (high level)

**On slide:**

- Correctness · grain · lineage hygiene · communication

**Speaker notes:**

Walk the four criteria quickly: **correctness** (`dbt parse/run/test`), **grain** (sentences that match joins), **lineage hygiene** (`ref`/`source` not hard-coded paths), **communication** (YAML descriptions stakeholders understand). Offer **peer review** pairs for 10 minutes if time.

---

## Slide 48 — Mock interview Q1

**On slide:**

- Walk file → KPI on a dashboard (60 seconds)

**Speaker notes:**

Cold-call one volunteer **60 seconds**. Correct answer touches **ingest → Bronze → Silver → dbt mart → SQL or Streamlit** with **grain**. Debrief gently: **brevity** and **order** beat buzzwords.

---

## Slide 49 — Mock interview Q2

**On slide:**

- Where do you test: Python vs dbt vs integration?

**Speaker notes:**

Ideal answer: **layered strategy** — Python for **pure transforms**, dbt for **relational contracts**, integration/smoke for **DAG** and **critical paths**. Discuss **cost vs confidence** trade‑offs honestly.

---

## Slide 50 — Mock interview Q3

**On slide:**

- Migrate this repo to Databricks — what changes first?

**Speaker notes:**

Anchor on **paths + adapters + orchestration**: **`profiles.yml`**, **`dbt-databricks`**, **Unity Catalog**, **job parameters**, **`abfss`**, **secrets**. **Ingest** may become **notebooks/jobs** with **ADF** triggers. Avoid pretending **one checkbox** migrates everything.

---

## Slide 51 — Stretch topics (if time)

**On slide:**

- Incremental models · SCD2 · streaming ingestion
- Unity Catalog governance patterns

**Speaker notes:**

Use only if ahead of schedule. Position as **“week two of a real job”** topics — name them so learners can **self-study**. Do not promise hands‑on here unless you add lab time.

---

## Slide 52 — Homework pack (optional)

**On slide:**

- Read `CONCEPTS_AND_PURPOSE.md`
- Run one stage with intentional failure + fix write-up

**Speaker notes:**

Homework reinforces **reading** and **debugging narrative**. Intentional failure examples: unset **`DELTA_LAKE_PATH`**, delete Silver path, run **`dbt test`** expecting red then fix. Ask for a **half-page postmortem** — builds senior communication tone.

---

## Slide 53 — Q&A + next steps

**On slide:**

- Point to `docs/training/COMPLETE_TECHNICAL_TRAINER_GUIDE.md`
- Thank you / office hours

**Speaker notes:**

Close the loop: **primary doc** for trainers, **LEARNING_GUIDE** for learners, **COURSE_MARKETING** for cohort story. Thank TAs/host; share **office hours** / forum / chat channel if applicable.

---

## Appendix A — Screenshot: `pytest` green (optional slide)

**On slide:**

- (Insert terminal screenshot)

**Speaker notes:**

Capture **`pytest tests/test_transformations.py -q`** or a subset green. Narrate: **fast feedback** at Python boundary — this is **CI bait** for portfolios.

---

## Appendix B — Screenshot: Streamlit heatmap (optional slide)

**On slide:**

- (Insert dashboard screenshot)

**Speaker notes:**

Pick a chart that tells a **pattern story** — explain **grain** of underlying mart and **why** heatmap encodes that question. Warn against **chartjunk**; emphasize **decision support**.

---

## Appendix C — Screenshot: `dbt test` failure (optional slide)

**On slide:**

- (Insert red test output)

**Speaker notes:**

**Failure slides** reduce fear of red tests. Walk how to read **which model**, **which test**, **which SQL**. Show the **fix path**: adjust model vs adjust test vs fix upstream Silver.

---

## Appendix D — Diagram: README Mermaid (optional slide)

**On slide:**

- (Export PNG from root `README.md` architecture diagram)

**Speaker notes:**

Use repository **Appendix A** mermaid from the trainer guide as the canonical **big picture** export. Ask learners to **annotate** the PNG with their own cohort date and **one** personal learning goal — cheap engagement, strong retention.

---

*Manuscript ends. Update slide numbering if you insert regional/housekeeping slides at the front.*
