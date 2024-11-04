-- Inventory Reorder Alerts KPI Query
-- Flags items below reorder level and identifies critical items (quantity = 0)
-- per warehouse, program, and item type.
-- Executable: duckdb pspl.duckdb < sql/inventory_reorder_alerts.sql

WITH item_flags AS (
    SELECT
        warehouse,
        program,
        item_type,
        item_name,
        quantity,
        reorder_level,
        CASE WHEN quantity < reorder_level THEN 1 ELSE 0 END    AS is_below_reorder,
        CASE WHEN quantity = 0 THEN item_name ELSE NULL END      AS critical_item_name
    FROM main.stg_inventory
),

aggregated AS (
    SELECT
        warehouse,
        program,
        item_type,
        COUNT(*)                                                AS total_items,
        SUM(is_below_reorder)                                   AS items_below_reorder,
        SUM(is_below_reorder) / NULLIF(COUNT(*), 0) * 1.0      AS alert_pct,
        STRING_AGG(critical_item_name, ', ')
            FILTER (WHERE critical_item_name IS NOT NULL)       AS critical_items
    FROM item_flags
    GROUP BY warehouse, program, item_type
)

SELECT
    warehouse,
    program,
    item_type,
    total_items,
    items_below_reorder,
    ROUND(alert_pct, 4)     AS alert_pct,
    critical_items
FROM aggregated
ORDER BY warehouse, program, item_type;
