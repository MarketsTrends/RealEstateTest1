from __future__ import annotations

from typing import Any

from app.schemas import PropertyType


def fetch_sales_comps(
    conn: Any,
    *,
    lat: float,
    lon: float,
    radius_m: int,
    months_back: int,
    property_type: PropertyType,
    surface_m2: float | None,
    surface_tolerance_pct: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    filters = ""
    params: dict[str, Any] = {
        "lat": lat,
        "lon": lon,
        "radius_m": radius_m,
        "months_back": months_back,
    }
    if property_type != PropertyType.unknown:
        filters += " AND property_type = %(property_type)s"
        params["property_type"] = property_type.value
    if surface_m2 is not None:
        min_s = surface_m2 * (1 - surface_tolerance_pct)
        max_s = surface_m2 * (1 + surface_tolerance_pct)
        filters += " AND surface_m2 BETWEEN %(surface_min)s AND %(surface_max)s"
        params["surface_min"] = min_s
        params["surface_max"] = max_s

    sql = f"""
    WITH base AS (
      SELECT
        transaction_id,
        sold_at::date AS sold_at,
        price_eur,
        surface_m2,
        rooms,
        COALESCE(property_type, 'unknown') AS property_type,
        ST_Distance(
          geom::geography,
          ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326)::geography
        ) AS distance_m,
        CASE WHEN surface_m2 > 0 THEN price_eur/surface_m2 ELSE NULL END AS price_per_sqm
      FROM sales_transactions
      WHERE sold_at >= CURRENT_DATE - ((%(months_back)s::text || ' months')::interval)
        AND ST_DWithin(
          geom::geography,
          ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326)::geography,
          %(radius_m)s
        )
        {filters}
    )
    SELECT
      (SELECT COUNT(*) FROM base) AS n,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY price_per_sqm) FROM base) AS median_price_per_sqm_eur,
      (SELECT percentile_cont(0.25) WITHIN GROUP (ORDER BY price_per_sqm) FROM base) AS p25_price_per_sqm_eur,
      (SELECT percentile_cont(0.75) WITHIN GROUP (ORDER BY price_per_sqm) FROM base) AS p75_price_per_sqm_eur,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY price_eur) FROM base) AS median_price_eur,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY surface_m2) FROM base) AS median_surface_m2;
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        stats = {
            "n": int(row[0]) if row and row[0] is not None else 0,
            "median_price_per_sqm_eur": float(row[1]) if row and row[1] is not None else None,
            "p25_price_per_sqm_eur": float(row[2]) if row and row[2] is not None else None,
            "p75_price_per_sqm_eur": float(row[3]) if row and row[3] is not None else None,
            "median_price_eur": float(row[4]) if row and row[4] is not None else None,
            "median_surface_m2": float(row[5]) if row and row[5] is not None else None,
        }

        comps_sql = f"""
        SELECT
          transaction_id,
          sold_at::date,
          price_eur,
          surface_m2,
          rooms,
          COALESCE(property_type, 'unknown') AS property_type,
          ST_Distance(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326)::geography
          ) AS distance_m
        FROM sales_transactions
        WHERE sold_at >= CURRENT_DATE - ((%(months_back)s::text || ' months')::interval)
          AND ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326)::geography,
            %(radius_m)s
          )
          {filters}
        ORDER BY distance_m ASC
        LIMIT 50
        """
        cur.execute(comps_sql, params)
        comps = []
        for r in cur.fetchall():
            comps.append(
                {
                    "transaction_id": str(r[0]),
                    "sold_at": r[1],
                    "price_eur": float(r[2]),
                    "surface_m2": float(r[3]) if r[3] is not None else None,
                    "rooms": int(r[4]) if r[4] is not None else None,
                    "property_type": r[5],
                    "distance_m": float(r[6]),
                }
            )

    return stats, comps
