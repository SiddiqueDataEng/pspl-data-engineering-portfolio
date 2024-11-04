# Data engineering trainer pack

This folder is a **complete technical guideline** for anyone teaching this repository as a **hands-on data engineering** course (lakehouse patterns, PySpark + Delta, dbt, DuckDB, testing, and operations).

| Document | Use it for |
|----------|------------|
| [COMPLETE_TECHNICAL_TRAINER_GUIDE.md](COMPLETE_TECHNICAL_TRAINER_GUIDE.md) | **Primary reference:** learning outcomes, agendas, concepts, every tool/technique mapped to repo paths, lab scripts, assessments, classroom troubleshooting |
| [COURSE_MARKETING.md](COURSE_MARKETING.md) | **Marketing / cohort comms:** titles, elevator pitch, local vs cloud-ready narrative, FAQ, email templates, **10-day syllabus** table |
| [TRAINER_SLIDES_WITH_SPEAKER_NOTES.md](TRAINER_SLIDES_WITH_SPEAKER_NOTES.md) | **Slide manuscript:** same slide order as the outline, each with **on-slide bullets + speaker notes** (Marp / import-friendly) |
| [SLIDE_DECK_OUTLINE.md](SLIDE_DECK_OUTLINE.md) | **Compact outline:** titles and bullets only — pair with speaker-notes manuscript above |
| [pspl_trainer_overview.pptx](pspl_trainer_overview.pptx) | **PowerPoint (regenerable):** short overview deck — run `python scripts/generate_pspl_trainer_deck.py` from repo root after `pip install -r requirements.txt` |

**Learner-facing docs** (assign as pre-reading or homework) live one level up: [../README.md](../README.md), [../CONCEPTS_AND_PURPOSE.md](../CONCEPTS_AND_PURPOSE.md), [../LEARNING_GUIDE.md](../LEARNING_GUIDE.md), [../JUPYTER_AND_NOTEBOOKS.md](../JUPYTER_AND_NOTEBOOKS.md). For **live demo command parity** with labs, use the single matrix [../RUN_EACH_COMPONENT.md](../RUN_EACH_COMPONENT.md).

---

## How trainers should use this pack

1. Read **Section 1–3** of the master guide (outcomes, audiences, agendas) and pick a **duration** (1-day executive overview vs 3–5 day engineering deep dive). For a **10-day** public narrative, start from [COURSE_MARKETING.md](COURSE_MARKETING.md). Skim [SCOPE_AND_CLOUD.md](../SCOPE_AND_CLOUD.md) for cohort boundaries and cloud mapping.
2. Align **Day N** blocks with the **session lab script** in the master guide; each block lists **trainer talking points**, **live demo commands**, and **learner deliverables**.
3. Build slides from **[TRAINER_SLIDES_WITH_SPEAKER_NOTES.md](TRAINER_SLIDES_WITH_SPEAKER_NOTES.md)** (notes + bullets) or import **[SLIDE_DECK_OUTLINE.md](SLIDE_DECK_OUTLINE.md)** if you only need titles; extend diagrams with the Mermaid charts from the repo [README.md](../../README.md).
4. Keep the [LEARNING_GUIDE.md](../LEARNING_GUIDE.md) open during Windows labs for `JAVA_HOME`, `DELTA_LAKE_PATH`, and execution policy.

---

## Suggested cohort logistics

- **Machines:** Windows 10/11 or macOS/Linux; **Python 3.11**, **JDK 11/17**, **8 GB+ RAM**; first Spark run needs **network** (Maven JARs).
- **DuckDB CLI:** optional for KPI lab; Windows learners can use `scripts/run-sql-kpis.ps1`.
- **Artifacts:** learners should `make clean` / `scripts/clean-artifacts.ps1` between major retries to avoid stale Delta handles on Windows.

---

## Versioning

This pack matches the repository layout and tooling pinned in `requirements.txt`. When you upgrade PySpark, dbt, or DuckDB, revisit the **cloud mapping** and **troubleshooting** sections of the master guide.
