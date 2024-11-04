
  
  create view "pspl"."main"."stg_inventory__dbt_tmp" as (
    with source as (
    select * from delta_scan('C:/Users/Siddique/Desktop/Pakistani social protection landscape/delta_lake/silver/inventory')
),

transformed as (
    select
        item_id,
        item_name,
        item_type,
        unit,
        warehouse,
        program,
        supplier,

        -- Type casts
        CAST(quantity AS INTEGER)           as quantity,
        CAST(reorder_level AS INTEGER)      as reorder_level,
        CAST(last_updated AS TIMESTAMP)     as last_updated

    from source
)

select * from transformed
  );
