# Jupyter notebook environment

This project already lists **Jupyter**, **JupyterLab**, and **nbconvert** in [`requirements.txt`](../requirements.txt). After `pip install -r requirements.txt` (or `.\setup.ps1`), you have everything needed for **interactive** notebooks and for **headless** notebook execution in the pipeline.

---

## 1. Virtual environment as the “kernel”

**Recommended:** Use the project `.venv` so PySpark, Delta, dbt, DuckDB, and plotting libraries match the versions this repo was tested with.

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import pyspark, duckdb; print('ok')"
```

Jupyter will use whichever `python` is first on `PATH` after activation—that is effectively your **kernel**.

---

## 2. JupyterLab (interactive exploration)

From the **repository root** with the venv active:

```powershell
python -m jupyter lab
```

Then open:

| Notebook | Purpose |
|----------|---------|
| [`notebooks/00_onboarding_tour.ipynb`](../notebooks/00_onboarding_tour.ipynb) | Story-led tour: what each folder does, suggested order, optional checks **without** starting Spark |
| [`notebooks/delta_lake_operations.ipynb`](../notebooks/delta_lake_operations.ipynb) | Full **Bronze → Silver** PySpark + Delta + charts (also executed by the pipeline via nbconvert) |

**Why repo root:** Paths in `delta_lake_operations.ipynb` resolve `delta_lake/` and `docs/sample_outputs/` relative to the repo layout. Starting Jupyter from the root avoids “file not found” surprises.

---

## 3. nbconvert (how CI and `make` run the Spark notebook)

The Makefile and `scripts/run-full-pipeline.ps1` run (from repo root):

```text
python -m jupyter nbconvert --to notebook --execute notebooks/delta_lake_operations.ipynb --output-dir notebooks --output delta_lake_operations_executed.ipynb
```

**What this does:** Starts a fresh Python process, runs every cell top to bottom, writes an executed copy to `notebooks/delta_lake_operations_executed.ipynb`.

**Do not** pass `--output notebooks/delta_lake_operations_executed.ipynb`: nbconvert treats that path as **relative to the notebook’s folder**, so you get `notebooks/notebooks/...` and a `FileNotFoundError`. Use **`--output-dir notebooks --output delta_lake_operations_executed.ipynb`** (or only the basename `--output delta_lake_operations_executed.ipynb`, which lands next to the source under `notebooks/`).

**Implications:**

- Long Spark sessions are restarted each time—good for reproducibility, slower for iterative edits.
- The notebook sets `matplotlib` to the **Agg** backend so charts render without a display during batch execution.

For day-to-day learning, prefer **JupyterLab** and run cells manually; use **nbconvert** when you want a repeatable “batch job” like production.

### Noisy but usually harmless messages (Windows + Spark)

After a successful run you may still see:

- **`RuntimeWarning: Proactor event loop... zmq`:** Jupyter on Windows; optional fix is `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` before starting the loop (not required for a successful nbconvert).
- **`WARN MemoryManager: Total allocation exceeds 95%`:** Spark is close to the default JVM heap; the notebook still completes on typical laptops.
- **`Exception while deleting Spark temp dir` ... `Failed to delete` ... `.jar`:** Windows file locking during JVM shutdown; Spark logs it as non-fatal. **`ERROR: The process "…" not found`:** Often follows a `taskkill`-style cleanup when the process already exited—ignore if the notebook file was written.

---

## 4. Java and Windows notes (Spark notebooks only)

The **onboarding** notebook is mostly markdown. The **Delta** notebook needs:

- **JDK 11 or 17** and `JAVA_HOME`
- On Windows, **`HADOOP_HOME`** and **`winutils.exe`** (the full pipeline script configures these)

If Spark fails to start in Jupyter, compare your environment to [LEARNING_GUIDE.md — Section 4–7](LEARNING_GUIDE.md#4-prerequisites-read-before-first-run).

---

## 5. Streamlit dashboard (story-led KPIs)

After **`dbt run`** has created `pspl.duckdb` at the repo root, launch:

```powershell
.\scripts\run-dashboard.ps1
```

Or manually (venv active, repo root):

```powershell
streamlit run dashboard/streamlit_app.py
```

The app loads marts such as `mart_payment_kpis` and `mart_donor_budget_vs_actual` and plots **Plotly** charts. If the database file is missing, the UI explains that you need to run the pipeline first.

---

## 6. Optional: register a dedicated Jupyter kernel

If you want a named kernel in the UI:

```powershell
python -m ipykernel install --user --name=PSPL-portfolio --display-name="PSPL portfolio (venv)"
```

Then pick **“PSPL portfolio (venv)”** as the kernel in JupyterLab. This is optional; many learners rely on “Python 3” from the activated venv alone.

---

## Related

- [docs/README.md](README.md) — documentation hub and learning path
- [LEARNING_GUIDE.md](LEARNING_GUIDE.md) — full setup and stage-by-stage runs
- [runbooks/dbt_runbook.md](runbooks/dbt_runbook.md) — `DELTA_LAKE_PATH` and dbt operations
