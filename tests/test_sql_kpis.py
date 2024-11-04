"""
SQL KPI formula correctness tests.

Feature: PSPL-data-engineering-portfolio
"""

import duckdb
import pytest
from hypothesis import given, settings, HealthCheck, strategies as st
from datetime import date
from itertools import groupby


# ---------------------------------------------------------------------------
# Property 11 – Budget utilization formula correctness
# Validates: Requirements 4.2
# ---------------------------------------------------------------------------

@pytest.mark.property
@given(st.lists(
    st.tuples(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.floats(min_value=1.0, max_value=1e8, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=1e8, allow_nan=False, allow_infinity=False)
    ),
    min_size=1,
    max_size=200
))
@settings(max_examples=100, deadline=None)
def test_budget_utilization_formula_correctness(donor_program_data):
    """
    Property 11: Budget utilization formula correctness

    For any donor-program combination where committed > 0, the utilization_pct
    value SHALL equal (disbursed / committed) * 100 within ±0.001, and variance
    SHALL equal committed - disbursed.

    Feature: PSPL-data-engineering-portfolio, Property 11: Budget utilization formula correctness
    Validates: Requirements 4.2
    """
    conn = duckdb.connect(":memory:")
    try:
        # Create table with donor/program/committed/disbursed data
        conn.execute("""
            CREATE TABLE donor_reports (
                donor VARCHAR,
                program VARCHAR,
                amount_committed DOUBLE,
                amount_disbursed DOUBLE
            )
        """)

        # Insert generated data
        conn.executemany(
            "INSERT INTO donor_reports VALUES (?, ?, ?, ?)",
            [(donor, program, committed, disbursed)
             for donor, program, committed, disbursed in donor_program_data]
        )

        # Execute SQL query that computes utilization_pct and variance
        result = conn.execute("""
            SELECT
                donor,
                program,
                SUM(amount_committed) AS total_committed,
                SUM(amount_disbursed) AS total_disbursed,
                SUM(amount_committed) - SUM(amount_disbursed) AS variance,
                SUM(amount_disbursed) / NULLIF(SUM(amount_committed), 0) * 100 AS utilization_pct
            FROM donor_reports
            GROUP BY donor, program
        """).fetchall()

        # Verify formula correctness for each row
        for row in result:
            donor, program, total_committed, total_disbursed, variance, utilization_pct = row

            if total_committed > 0:
                expected_utilization = (total_disbursed / total_committed) * 100
                assert abs(utilization_pct - expected_utilization) < 0.001, (
                    f"Utilization % mismatch for {donor}/{program}: "
                    f"expected {expected_utilization:.4f}, got {utilization_pct:.4f}"
                )

            expected_variance = total_committed - total_disbursed
            assert abs(variance - expected_variance) < 0.001, (
                f"Variance mismatch for {donor}/{program}: "
                f"expected {expected_variance:.4f}, got {variance:.4f}"
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Property 12 – Payment success rate bounds
# Validates: Requirements 4.3
# ---------------------------------------------------------------------------

@pytest.mark.property
@given(st.lists(
    st.tuples(
        st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.sampled_from(['Success', 'Failed', 'Pending'])
    ),
    min_size=10,
    max_size=500
))
@settings(max_examples=100, deadline=None)
def test_payment_success_rate_bounds(payment_data):
    """
    Property 12: Payment success rate bounds

    For any district-program-month combination, the success_rate value SHALL
    be in [0.0, 1.0], and the rolling_3m_avg_success_rate SHALL also be in
    [0.0, 1.0].

    Feature: PSPL-data-engineering-portfolio, Property 12: Payment success rate bounds
    Validates: Requirements 4.3
    """
    conn = duckdb.connect(":memory:")
    try:
        # Create payments table
        conn.execute("""
            CREATE TABLE payments (
                payment_date DATE,
                district VARCHAR,
                program VARCHAR,
                payment_status VARCHAR
            )
        """)

        # Insert generated data
        conn.executemany(
            "INSERT INTO payments VALUES (?, ?, ?, ?)",
            [(payment_date, district, program, status)
             for payment_date, district, program, status in payment_data]
        )

        # Execute SQL query computing success_rate and rolling average
        result = conn.execute("""
            WITH monthly_rates AS (
                SELECT
                    district,
                    program,
                    DATE_TRUNC('month', payment_date) AS month,
                    COUNT(*) AS total_payments,
                    SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END) AS successful_payments,
                    SUM(CASE WHEN payment_status = 'Success' THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0) * 1.0 AS success_rate
                FROM payments
                GROUP BY district, program, DATE_TRUNC('month', payment_date)
            )
            SELECT
                district,
                program,
                month,
                total_payments,
                successful_payments,
                success_rate,
                AVG(success_rate) OVER (
                    PARTITION BY district, program
                    ORDER BY month
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) AS rolling_3m_avg_success_rate
            FROM monthly_rates
            ORDER BY district, program, month
        """).fetchall()

        # Verify bounds for all rows
        for row in result:
            district, program, month, total_payments, successful_payments, success_rate, rolling_avg = row

            assert 0.0 <= success_rate <= 1.0, (
                f"Success rate out of bounds for {district}/{program}/{month}: {success_rate}"
            )

            assert 0.0 <= rolling_avg <= 1.0, (
                f"Rolling 3m avg out of bounds for {district}/{program}/{month}: {rolling_avg}"
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Property 13 – Vulnerability decile partitioning
# Validates: Requirements 4.4
# ---------------------------------------------------------------------------

@pytest.mark.property
@given(st.lists(
    st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    min_size=20,
    max_size=500
))
@settings(max_examples=100, deadline=None)
def test_vulnerability_decile_partitioning(vulnerability_scores):
    """
    Property 13: Vulnerability decile partitioning

    For any set of vulnerability scores, when segmented into deciles using
    NTILE(10), each decile value SHALL be between 1 and 10, and decile
    boundaries SHALL be monotonically non-decreasing (higher decile = higher
    or equal score).

    Feature: PSPL-data-engineering-portfolio, Property 13: Vulnerability decile partitioning
    Validates: Requirements 4.4
    """
    conn = duckdb.connect(":memory:")
    try:
        # Create refugees table
        conn.execute("""
            CREATE TABLE refugees (
                refugee_id INTEGER,
                vulnerability_score DOUBLE
            )
        """)

        # Insert generated data
        conn.executemany(
            "INSERT INTO refugees VALUES (?, ?)",
            [(idx, score) for idx, score in enumerate(vulnerability_scores)]
        )

        # Execute SQL query using NTILE(10) to compute deciles
        result = conn.execute("""
            SELECT
                refugee_id,
                vulnerability_score,
                NTILE(10) OVER (ORDER BY vulnerability_score) AS decile
            FROM refugees
            ORDER BY decile, vulnerability_score
        """).fetchall()

        # Verify decile values are in [1, 10]
        for row in result:
            refugee_id, score, decile = row
            assert 1 <= decile <= 10, (
                f"Decile out of range for refugee {refugee_id}: {decile}"
            )

        # Verify decile boundaries are monotonically non-decreasing
        # Group by decile and check min/max scores
        decile_stats = conn.execute("""
            WITH deciles AS (
                SELECT
                    vulnerability_score,
                    NTILE(10) OVER (ORDER BY vulnerability_score) AS decile
                FROM refugees
            )
            SELECT
                decile,
                MIN(vulnerability_score) AS min_score,
                MAX(vulnerability_score) AS max_score
            FROM deciles
            GROUP BY decile
            ORDER BY decile
        """).fetchall()

        prev_max = None
        for decile, min_score, max_score in decile_stats:
            if prev_max is not None:
                # Current decile's min should be >= previous decile's max
                # (allowing for ties at boundaries)
                assert min_score >= prev_max or abs(min_score - prev_max) < 1e-9, (
                    f"Decile {decile} min score {min_score} < previous max {prev_max}"
                )
            prev_max = max_score
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Property 14 – Protection caseload cumulative monotonicity
# Validates: Requirements 4.5
# ---------------------------------------------------------------------------

@pytest.mark.property
@given(st.lists(
    st.tuples(
        st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.integers(min_value=1, max_value=100)
    ),
    min_size=10,
    max_size=300
))
@settings(max_examples=100, deadline=None)
def test_protection_caseload_cumulative_monotonicity(case_data):
    """
    Property 14: Protection caseload cumulative monotonicity

    For any ordered sequence of protection cases ordered by incident_month,
    the cumulative_cases column SHALL be monotonically non-decreasing within
    each incident_type partition.

    Feature: PSPL-data-engineering-portfolio, Property 14: Protection caseload cumulative monotonicity
    Validates: Requirements 4.5
    """
    conn = duckdb.connect(":memory:")
    try:
        # Create protection cases table
        conn.execute("""
            CREATE TABLE protection_cases (
                incident_date DATE,
                incident_type VARCHAR,
                case_count INTEGER
            )
        """)

        # Insert generated data
        conn.executemany(
            "INSERT INTO protection_cases VALUES (?, ?, ?)",
            [(incident_date, incident_type, case_count)
             for incident_date, incident_type, case_count in case_data]
        )

        # Execute SQL query computing cumulative cases
        result = conn.execute("""
            WITH monthly_cases AS (
                SELECT
                    incident_type,
                    DATE_TRUNC('month', incident_date) AS incident_month,
                    SUM(case_count) AS total_cases
                FROM protection_cases
                GROUP BY incident_type, DATE_TRUNC('month', incident_date)
            )
            SELECT
                incident_type,
                incident_month,
                total_cases,
                SUM(total_cases) OVER (
                    PARTITION BY incident_type
                    ORDER BY incident_month
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS cumulative_cases
            FROM monthly_cases
            ORDER BY incident_type, incident_month
        """).fetchall()

        # Verify monotonicity within each incident_type partition
        for incident_type, group in groupby(result, key=lambda x: x[0]):
            cumulative_values = [row[3] for row in group]  # cumulative_cases is 4th column

            for i in range(1, len(cumulative_values)):
                assert cumulative_values[i] >= cumulative_values[i - 1], (
                    f"Cumulative cases not monotonic for {incident_type}: "
                    f"{cumulative_values[i]} < {cumulative_values[i - 1]} at position {i}"
                )
    finally:
        conn.close()
