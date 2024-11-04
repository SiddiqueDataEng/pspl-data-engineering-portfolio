"""
Interactive KPI dashboard over dbt marts in pspl.duckdb.

Run from repo root (venv active):
  streamlit run dashboard/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "pspl.duckdb"

PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "responsive": True,
}


@st.cache_data(ttl=120)
def query_df(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def render_story_header() -> None:
    st.markdown("---")
    st.markdown("### Story: from raw files to these charts")

    st.markdown(
        dedent(
            """
            #### 1. Data sources (what sits upstream)

            The **inputs** are nine **synthetic** files under `data_large/` in this repository. They mimic
            a Pakistani **social protection** and **Afghan refugee** assistance context: compressed CSV,
            Parquet, JSON, and Avro — the kinds of shapes real programmes receive from partners, surveys,
            and operational systems. **Numbers and names are fictional**; grains and joins are realistic
            for practice only.
            """
        ).strip()
    )

    st.markdown(
        dedent(
            """
            #### 2. Data engineering (how numbers become trustworthy tables)

            **Bronze** — `ingest/ingest.py` reads each file with the right reader, lands **Delta** tables under
            `delta_lake/bronze/` (a durable, queryable copy of what arrived).

            **Silver** — `notebooks/delta_lake_operations.ipynb` cleans, deduplicates, and standardises types,
            writing **Silver** Delta under `delta_lake/silver/`.

            **Gold** — **dbt** models (`stg_*` → `int_*` → `mart_*`) read Silver through DuckDB’s `delta_scan`,
            then materialise **marts** into `pspl.duckdb` at the repo root.

            This dashboard reads only the **`mart_*`** layer: analyst-ready, KPI-oriented tables — not raw files.
            """
        ).strip()
    )

    st.markdown(
        dedent(
            """
            #### 3. How to use the charts (interactivity)

            **Zoom / pan:** click-drag on the chart area; double-click resets. **Legend:** click a series name
            to hide or show it. **Hover:** each trace shows exact values. **Heatmaps** give a **whole-period**
            view; **ranked bars** show a **single-month snapshot**; **line + volume** pairs rate with **how many**
            payments sat behind that rate so small samples are visible.
            """
        ).strip()
    )
    st.markdown("---")


def render_sidebar() -> None:
    with st.sidebar:
        st.header("How to run this locally")
        st.markdown(
            dedent(
                """
                - **Full build (Windows):** `scripts\\run-full-pipeline.ps1`
                - **Docs:** `docs/README.md`, `docs/CONCEPTS_AND_PURPOSE.md`
                - **Notebook tour:** `notebooks/00_onboarding_tour.ipynb`
                """
            ).strip()
        )
        st.caption(f"DuckDB file: `{DB_PATH.name}`")


def _month_range_slider(df: pd.DataFrame, col: str, key: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    s = pd.to_datetime(df[col])
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi):
        return lo, hi
    if lo.normalize() == hi.normalize():
        st.caption(f"Single month in data: **{lo.date()}** (no range slider).")
        return pd.Timestamp(lo), pd.Timestamp(hi)
    picked = st.slider(
        "Month range (filters all charts in this tab)",
        min_value=lo.to_pydatetime(),
        max_value=hi.to_pydatetime(),
        value=(lo.to_pydatetime(), hi.to_pydatetime()),
        format="YYYY-MM",
        key=key,
    )
    return pd.Timestamp(picked[0]), pd.Timestamp(picked[1])


def tab_payments() -> None:
    st.subheader("Payments — success rate, volume, and comparisons")
    st.markdown(
        dedent(
            """
            **Mart:** `mart_payment_kpis` — month × district × programme with counts, **success_rate**, and
            **rolling_3m_avg_success_rate**. Use the **heatmap** for the full grid, **ranked bars** for the latest
            month in your range, and **lines + volume** for a focused district set.
            """
        ).strip()
    )
    try:
        pay_df = query_df(
            """
            SELECT reporting_month, district, program, total_payments,
                   successful_payments, success_rate, rolling_3m_avg_success_rate
            FROM main.mart_payment_kpis
            ORDER BY reporting_month, district
            """
        )
    except Exception as exc:
        st.warning(f"Could not read mart_payment_kpis: {exc}")
        return
    if pay_df.empty:
        st.info("No rows returned from mart_payment_kpis.")
        return

    pay_df = pay_df.copy()
    pay_df["reporting_month"] = pd.to_datetime(pay_df["reporting_month"])

    programs = sorted(pay_df["program"].dropna().unique())
    prog = st.selectbox("Programme", programs, key="pay_prog")
    dff = pay_df[pay_df["program"] == prog]

    t0, t1 = _month_range_slider(dff, "reporting_month", "pay_month_range")
    dff = dff[(dff["reporting_month"] >= t0) & (dff["reporting_month"] <= t1)]

    if dff.empty:
        st.warning("No rows in the selected month range.")
        return

    districts = sorted(dff["district"].dropna().unique())
    default_n = min(6, len(districts))
    selected = st.multiselect(
        "Districts for line + volume charts (pick a small set to reduce overlap)",
        districts,
        default=districts[:default_n],
        key="pay_districts",
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Success rate grid (district × month)")
        pivot = dff.pivot_table(
            index="district",
            columns="reporting_month",
            values="success_rate",
            aggfunc="mean",
        )
        pivot = pivot.reindex(sorted(pivot.index))
        pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: pd.Timestamp(x)), axis=1)
        fig_hm = px.imshow(
            pivot,
            labels=dict(x="Month", y="District", color="Success rate"),
            color_continuous_scale="RdYlGn",
            zmin=0,
            zmax=1,
            aspect="auto",
            title=f"Heatmap — {prog}",
        )
        fig_hm.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_hm, use_container_width=True, config=PLOTLY_CONFIG)

    with c2:
        st.markdown("##### Latest month in range — success rate (ranked)")
        last_m = dff["reporting_month"].max()
        snap = dff[dff["reporting_month"] == last_m].sort_values("success_rate", ascending=True)
        fig_bar = px.bar(
            snap,
            x="success_rate",
            y="district",
            orientation="h",
            text=snap["success_rate"].map(lambda v: f"{v:.0%}"),
            title=f"Success rate by district — {last_m.date()} — {prog}",
            color="success_rate",
            color_continuous_scale="RdYlGn",
            range_color=(0, 1),
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(xaxis_tickformat=".0%", coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

    if selected:
        st.markdown("##### Spot rate vs 3-month average + payment volume")
        d_sel = dff[dff["district"].isin(selected)]
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.58, 0.42],
            vertical_spacing=0.07,
            subplot_titles=(
                "Success rate (solid) and rolling 3-month average (dashed)",
                "Total payments (volume behind the rate)",
            ),
        )
        palette = px.colors.qualitative.Set2 * 4
        for i, dist in enumerate(selected):
            sub = d_sel[d_sel["district"] == dist].sort_values("reporting_month")
            color = palette[i % len(palette)]
            fig.add_trace(
                go.Scatter(
                    x=sub["reporting_month"],
                    y=sub["success_rate"],
                    mode="lines+markers",
                    name=f"{dist} (month)",
                    legendgroup=dist,
                    line=dict(color=color),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=sub["reporting_month"],
                    y=sub["rolling_3m_avg_success_rate"],
                    mode="lines",
                    name=f"{dist} (3m avg)",
                    legendgroup=dist,
                    line=dict(color=color, dash="dash"),
                    showlegend=True,
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Bar(
                    x=sub["reporting_month"],
                    y=sub["total_payments"],
                    name=f"{dist} volume",
                    legendgroup=dist,
                    marker_color=color,
                    opacity=0.35,
                    showlegend=False,
                ),
                row=2,
                col=1,
            )
        fig.update_yaxes(tickformat=".0%", row=1, col=1)
        fig.update_layout(hovermode="x unified", height=640, barmode="overlay")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Select at least one district above to see the combined rate + volume chart.")

    with st.expander("Raw rows (filtered)"):
        st.dataframe(dff.sort_values(["reporting_month", "district"]), use_container_width=True, hide_index=True)


def tab_donors() -> None:
    st.subheader("Donors — committed vs disbursed and utilisation")
    st.markdown(
        dedent(
            """
            **Mart:** `mart_donor_budget_vs_actual`. **Bars** compare absolute **committed** and **disbursed** per donor.
            **Scatter** places each donor–programme point against the perfect-spend diagonal. **Heatmap** summarises
            **utilisation %** across the donor × programme grid.
            """
        ).strip()
    )
    try:
        donor_df = query_df(
            """
            SELECT donor, program, total_committed, total_disbursed,
                   variance, utilization_pct, utilization_rank
            FROM main.mart_donor_budget_vs_actual
            ORDER BY program, utilization_rank
            """
        )
    except Exception as exc:
        st.warning(f"Could not read mart_donor_budget_vs_actual: {exc}")
        return
    if donor_df.empty:
        st.info("No rows returned from mart_donor_budget_vs_actual.")
        return

    donor_df = donor_df.copy()
    progs = sorted(donor_df["program"].dropna().unique())
    prog_f = st.selectbox("Highlight one programme (charts use full table; scatter can filter)", progs, key="donor_prog")

    c1, c2 = st.columns(2)
    melted = donor_df.melt(
        id_vars=["donor", "program"],
        value_vars=["total_committed", "total_disbursed"],
        var_name="metric",
        value_name="amount",
    )
    melted["metric"] = melted["metric"].map(
        {"total_committed": "Committed", "total_disbursed": "Disbursed"}
    )
    sub_melt = melted[melted["program"] == prog_f]
    with c1:
        st.markdown(f"##### Committed vs disbursed (absolute) — {prog_f}")
        fig_b = px.bar(
            sub_melt,
            x="donor",
            y="amount",
            color="metric",
            barmode="group",
            title="Side-by-side currency totals",
        )
        fig_b.update_layout(hovermode="x unified")
        st.plotly_chart(fig_b, use_container_width=True, config=PLOTLY_CONFIG)

    with c2:
        st.markdown(f"##### Utilisation rank — {prog_f}")
        sub_rank = donor_df[donor_df["program"] == prog_f].sort_values("utilization_rank")
        fig_r = px.bar(
            sub_rank,
            x="donor",
            y="utilization_pct",
            text=sub_rank["utilization_pct"].map(lambda v: f"{v:.0%}"),
            title="Lower rank number = better utilisation within programme",
            color="utilization_rank",
            color_continuous_scale="Viridis_r",
        )
        fig_r.update_layout(yaxis_tickformat=".0%", hovermode="x unified")
        st.plotly_chart(fig_r, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("##### Scatter — committed (x) vs disbursed (y); diagonal = full utilisation")
    d_scat = donor_df[donor_df["program"] == prog_f] if st.toggle(
        "Restrict scatter to selected programme only", value=True, key="donor_scatter_toggle"
    ) else donor_df
    max_val = float(max(d_scat["total_committed"].max(), d_scat["total_disbursed"].max()) or 1.0)
    fig_s = px.scatter(
        d_scat,
        x="total_committed",
        y="total_disbursed",
        color="program",
        symbol="program",
        size="utilization_pct",
        hover_data=["donor", "variance", "utilization_rank"],
        title="Each point is one donor (colour = programme if showing all)",
    )
    fig_s.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode="lines",
            name="y = x (100% utilisation line)",
            line=dict(dash="dash", color="gray"),
        )
    )
    fig_s.update_layout(hovermode="closest", height=520)
    st.plotly_chart(fig_s, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("##### Utilisation % heatmap (donor × programme)")
    pivot_u = donor_df.pivot_table(
        index="donor",
        columns="program",
        values="utilization_pct",
        aggfunc="mean",
    )
    fig_u = px.imshow(
        pivot_u,
        labels=dict(x="Programme", y="Donor", color="Utilisation"),
        color_continuous_scale="Blues",
        zmin=0,
        zmax=1,
        aspect="auto",
        title="Share of committed funds disbursed",
    )
    fig_u.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_u, use_container_width=True, config=PLOTLY_CONFIG)

    with st.expander("Raw rows"):
        st.dataframe(donor_df, use_container_width=True, hide_index=True)


def tab_protection() -> None:
    st.subheader("Protection — caseload structure over time and by risk")
    st.markdown(
        dedent(
            """
            **Mart:** `mart_protection_caseload`. Charts below: **stacked area by risk** (same incident type),
            **heatmap district × month**, and **sunburst** for the latest month in your selected range (share of cases).
            """
        ).strip()
    )
    try:
        prot_df = query_df(
            """
            SELECT incident_month, incident_type, risk_level, host_district,
                   open_cases, total_cases, cumulative_cases
            FROM main.mart_protection_caseload
            ORDER BY incident_month
            """
        )
    except Exception as exc:
        st.warning(f"Could not read mart_protection_caseload: {exc}")
        return
    if prot_df.empty:
        st.info("No rows returned from mart_protection_caseload.")
        return

    prot_df = prot_df.copy()
    prot_df["incident_month"] = pd.to_datetime(prot_df["incident_month"])

    types = sorted(prot_df["incident_type"].dropna().unique())
    inc = st.selectbox("Incident type", types, key="prot_type")
    dff = prot_df[prot_df["incident_type"] == inc]

    t0, t1 = _month_range_slider(dff, "incident_month", "prot_month_range")
    dff = dff[(dff["incident_month"] >= t0) & (dff["incident_month"] <= t1)]
    if dff.empty:
        st.warning("No rows in the selected month range.")
        return

    risks = sorted(dff["risk_level"].dropna().unique())
    risk_sel = st.multiselect("Risk levels", risks, default=risks, key="prot_risks")
    dff = dff[dff["risk_level"].isin(risk_sel)]
    if dff.empty:
        st.warning("No rows after risk filter.")
        return

    agg = (
        dff.groupby(["incident_month", "risk_level"], as_index=False)[["open_cases", "total_cases"]]
        .sum()
        .sort_values("incident_month")
    )
    st.markdown("##### Stacked area — total cases by risk level (summed across districts)")
    fig_a = px.area(
        agg,
        x="incident_month",
        y="total_cases",
        color="risk_level",
        title=f"{inc} — cases by risk",
    )
    fig_a.update_layout(hovermode="x unified")
    st.plotly_chart(fig_a, use_container_width=True, config=PLOTLY_CONFIG)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Heatmap — district × month (total cases)")
        heat = dff.pivot_table(
            index="host_district",
            columns="incident_month",
            values="total_cases",
            aggfunc="sum",
        )
        heat = heat.reindex(sorted(heat.index))
        heat = heat.reindex(sorted(heat.columns, key=lambda x: pd.Timestamp(x)), axis=1)
        fig_h = px.imshow(
            heat,
            labels=dict(x="Month", y="Host district", color="Cases"),
            color_continuous_scale="Reds",
            aspect="auto",
            title="Where and when volume concentrates",
        )
        fig_h.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_h, use_container_width=True, config=PLOTLY_CONFIG)

    with c2:
        st.markdown("##### Open vs total cases (monthly totals)")
        agg2 = dff.groupby("incident_month", as_index=False)[["open_cases", "total_cases"]].sum()
        fig_l = go.Figure()
        fig_l.add_trace(
            go.Scatter(
                x=agg2["incident_month"],
                y=agg2["total_cases"],
                mode="lines+markers",
                name="Total cases",
            )
        )
        fig_l.add_trace(
            go.Scatter(
                x=agg2["incident_month"],
                y=agg2["open_cases"],
                mode="lines+markers",
                name="Open cases",
                line=dict(dash="dash"),
            )
        )
        fig_l.update_layout(
            title="Workload signal (open cases are a subset of total)",
            hovermode="x unified",
            height=420,
        )
        st.plotly_chart(fig_l, use_container_width=True, config=PLOTLY_CONFIG)

    last_m = dff["incident_month"].max()
    latest = dff[dff["incident_month"] == last_m]
    st.markdown(f"##### Sunburst — case mix in latest month ({last_m.date()})")
    if not latest.empty and latest["total_cases"].sum() > 0:
        fig_sb = px.sunburst(
            latest,
            path=["risk_level", "host_district"],
            values="total_cases",
            title="Share of cases: risk → district",
        )
        st.plotly_chart(fig_sb, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Not enough case volume for a sunburst in the latest month.")

    with st.expander("Raw rows (filtered)"):
        st.dataframe(dff.sort_values(["incident_month", "host_district"]), use_container_width=True, hide_index=True)


def tab_assistance() -> None:
    st.subheader("Refugee assistance — spend, reach, and modality mix")
    st.markdown(
        dedent(
            """
            **Mart:** `mart_refugee_assistance_summary`. **Scatter + marginals** shows reach vs spend with
            distributions; **bars** rank districts; **box** compares **average USD per delivery** by modality.
            """
        ).strip()
    )
    try:
        asst_df = query_df(
            """
            SELECT program, modality, host_district, total_beneficiaries,
                   total_amount_usd, avg_amount_usd, delivery_count,
                   avg_vulnerability_score
            FROM main.mart_refugee_assistance_summary
            ORDER BY host_district, program
            """
        )
    except Exception as exc:
        st.warning(f"Could not read mart_refugee_assistance_summary: {exc}")
        return
    if asst_df.empty:
        st.info("No rows returned from mart_refugee_assistance_summary.")
        return

    asst_df = asst_df.copy()
    progs = sorted(asst_df["program"].dropna().unique())
    prog = st.selectbox("Programme", progs, key="asst_prog")
    dff = asst_df[asst_df["program"] == prog]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Reach vs spend (marginal histograms)")
        fig_m = px.scatter(
            dff,
            x="total_beneficiaries",
            y="total_amount_usd",
            color="modality",
            size="delivery_count",
            hover_data=["host_district", "avg_amount_usd", "avg_vulnerability_score"],
            marginal_x="histogram",
            marginal_y="histogram",
            title=f"{prog} — each point is one district × modality row",
        )
        fig_m.update_layout(hovermode="closest", height=520)
        st.plotly_chart(fig_m, use_container_width=True, config=PLOTLY_CONFIG)

    with c2:
        st.markdown("##### Top districts by total USD (same programme)")
        top = dff.groupby("host_district", as_index=False)["total_amount_usd"].sum().nlargest(12, "total_amount_usd")
        fig_top = px.bar(
            top.sort_values("total_amount_usd"),
            x="total_amount_usd",
            y="host_district",
            orientation="h",
            title="Top 12 districts by summed spend",
        )
        st.plotly_chart(fig_top, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("##### Average USD per delivery — distribution by modality")
    fig_box = px.box(
        dff,
        x="modality",
        y="avg_amount_usd",
        color="modality",
        points="all",
        hover_data=["host_district", "delivery_count"],
        title="Box shows median and spread; points are districts",
    )
    fig_box.update_layout(showlegend=False, height=440)
    st.plotly_chart(fig_box, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("##### Heatmap — vulnerability vs spend intensity")
    heat = dff.pivot_table(
        index="host_district",
        columns="modality",
        values="total_amount_usd",
        aggfunc="sum",
    )
    fig_h = px.imshow(
        heat,
        labels=dict(x="Modality", y="District", color="Total USD"),
        color_continuous_scale="YlOrRd",
        aspect="auto",
        title=f"{prog} — total USD by district and modality",
    )
    fig_h.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_h, use_container_width=True, config=PLOTLY_CONFIG)

    with st.expander("Raw rows (filtered)"):
        st.dataframe(dff.sort_values(["host_district", "modality"]), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Social protection portfolio — KPIs",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Pakistani social protection & refugee assistance — KPI storyboard")
    st.markdown(
        "**Synthetic humanitarian-style portfolio** for learning **medallion** pipelines "
        "(Bronze/Silver Delta → **dbt** marts in DuckDB). "
        "Charts are **interactive** (zoom, pan, legend toggles, hover). Read the story, then explore each tab."
    )

    render_sidebar()
    render_story_header()

    if not DB_PATH.exists():
        st.error(
            f"**Database not found** at `{DB_PATH}`. "
            "Run `scripts/run-full-pipeline.ps1` (or ingest → Silver notebook → `dbt run`) so marts are built, "
            "then refresh this page."
        )
        st.stop()

    pay, donor, prot, asst = st.tabs(
        ["Payments", "Donors", "Protection", "Refugee assistance"]
    )

    with pay:
        tab_payments()
    with donor:
        tab_donors()
    with prot:
        tab_protection()
    with asst:
        tab_assistance()


if __name__ == "__main__":
    main()
