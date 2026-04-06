from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb


def insert_snapshot(
    conn: Any,
    *,
    snapshot_id: str,
    title: str,
    address_label: str | None,
    app_version: str,
    engine_version: str,
    request_payload: dict[str, Any],
    analysis_payload: dict[str, Any],
    comps_payload: dict[str, Any] | None,
    memo_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    sql = """
    INSERT INTO analysis_snapshots (
      id,
      title,
      address_label,
      app_version,
      engine_version,
      request_payload_json,
      analysis_response_json,
      comps_response_json,
      memo_response_json
    )
    VALUES (
      %(id)s,
      %(title)s,
      %(address_label)s,
      %(app_version)s,
      %(engine_version)s,
      %(request_payload)s,
      %(analysis_payload)s,
      %(comps_payload)s,
      %(memo_payload)s
    )
    RETURNING id::text, created_at, updated_at
    """
    params = {
        "id": snapshot_id,
        "title": title,
        "address_label": address_label,
        "app_version": app_version,
        "engine_version": engine_version,
        "request_payload": Jsonb(request_payload),
        "analysis_payload": Jsonb(analysis_payload),
        "comps_payload": Jsonb(comps_payload) if comps_payload is not None else None,
        "memo_payload": Jsonb(memo_payload) if memo_payload is not None else None,
    }

    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()

    conn.commit()
    return {
        "id": row[0],
        "created_at": row[1],
        "updated_at": row[2],
    }


def fetch_snapshot_by_id(conn: Any, snapshot_id: str) -> dict[str, Any] | None:
    sql = """
    SELECT
      id::text,
      created_at,
      updated_at,
      title,
      address_label,
      app_version,
      engine_version,
      request_payload_json,
      analysis_response_json,
      comps_response_json,
      memo_response_json
    FROM analysis_snapshots
    WHERE id = %(id)s
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"id": snapshot_id})
        row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "created_at": row[1],
        "updated_at": row[2],
        "title": row[3],
        "address_label": row[4],
        "app_version": row[5],
        "engine_version": row[6],
        "request": row[7],
        "analysis": row[8],
        "comps": row[9],
        "memo": row[10],
    }


def fetch_recent_snapshots(conn: Any, limit: int) -> list[dict[str, Any]]:
    sql = """
    SELECT
      id::text,
      created_at,
      updated_at,
      title,
      address_label,
      app_version,
      engine_version,
      (comps_response_json IS NOT NULL) AS has_comps,
      (memo_response_json IS NOT NULL) AS has_memo,
      memo_response_json->>'investment_view' AS investment_view
    FROM analysis_snapshots
    ORDER BY created_at DESC
    LIMIT %(limit)s
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"limit": limit})
        rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "title": row[3],
            "address_label": row[4],
            "app_version": row[5],
            "engine_version": row[6],
            "has_comps": bool(row[7]),
            "has_memo": bool(row[8]),
            "investment_view": row[9],
        }
        for row in rows
    ]
