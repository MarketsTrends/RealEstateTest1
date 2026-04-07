#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from dataclasses import dataclass
from datetime import date, datetime

import psycopg


@dataclass
class ImportRow:
    record_id: str
    transaction_id: str
    sold_at: date
    price_eur: float
    surface_m2: float | None
    rooms: int | None
    property_type: str
    lat: float
    lon: float
    source: str
    source_row_id: str | None


PARIS_POSTAL_PREFIX = "75"


def _pick(record: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return None


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def _property_type(value: str | None) -> str:
    if value is None:
        return "unknown"
    normalized = value.strip().lower()
    if "appart" in normalized:
        return "apartment"
    if "maison" in normalized or "house" in normalized:
        return "house"
    return "unknown"


def _record_id(*, source: str, source_row_id: str | None, txn_id: str, sold_at: date, lat: float, lon: float, price: float) -> str:
    if source_row_id:
        return f"{source}:{source_row_id}"
    raw = f"{source}|{txn_id}|{sold_at.isoformat()}|{lat:.6f}|{lon:.6f}|{price:.2f}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def parse_row(record: dict[str, str], source_name: str) -> ImportRow | None:
    postal_code = _pick(record, "postal_code", "code_postal", "code_postal_5")
    if not postal_code or not postal_code.startswith(PARIS_POSTAL_PREFIX):
        return None

    lat_raw = _pick(record, "lat", "latitude")
    lon_raw = _pick(record, "lon", "longitude", "lng")
    price_raw = _pick(record, "price_eur", "valeur_fonciere")
    sold_at_raw = _pick(record, "sold_at", "date_mutation", "date_vente")
    txn_raw = _pick(record, "transaction_id", "id_mutation", "id")
    source_row_id = _pick(record, "source_row_id", "id")

    if not all([lat_raw, lon_raw, price_raw, sold_at_raw, txn_raw]):
        return None

    lat = float(lat_raw.replace(",", "."))
    lon = float(lon_raw.replace(",", "."))
    price = float(price_raw.replace(" ", "").replace(",", "."))
    sold_at = _parse_date(sold_at_raw)

    if not (48.80 <= lat <= 48.91 and 2.20 <= lon <= 2.48):
        return None

    surface_raw = _pick(record, "surface_m2", "surface_reelle_bati")
    rooms_raw = _pick(record, "rooms", "nombre_pieces_principales")

    normalized_source_name = os.path.basename(source_name).strip().lower() or "unknown-file"
    source = f"dvf:{normalized_source_name}"
    return ImportRow(
        record_id=_record_id(
            source=source,
            source_row_id=source_row_id,
            txn_id=str(txn_raw),
            sold_at=sold_at,
            lat=lat,
            lon=lon,
            price=price,
        ),
        transaction_id=str(txn_raw),
        sold_at=sold_at,
        price_eur=price,
        surface_m2=float(surface_raw.replace(",", ".")) if surface_raw else None,
        rooms=int(float(rooms_raw)) if rooms_raw else None,
        property_type=_property_type(_pick(record, "property_type", "type_local")),
        lat=lat,
        lon=lon,
        source=source,
        source_row_id=source_row_id,
    )


def import_csv(path: str, database_url: str, truncate: bool) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    sql = """
    INSERT INTO sales_transactions (
      record_id, transaction_id, sold_at, price_eur, surface_m2, rooms, property_type, lat, lon, source, source_row_id
    ) VALUES (
      %(record_id)s, %(transaction_id)s, %(sold_at)s, %(price_eur)s, %(surface_m2)s, %(rooms)s, %(property_type)s,
      %(lat)s, %(lon)s, %(source)s, %(source_row_id)s
    )
    ON CONFLICT (record_id) DO UPDATE SET
      transaction_id = EXCLUDED.transaction_id,
      sold_at = EXCLUDED.sold_at,
      price_eur = EXCLUDED.price_eur,
      surface_m2 = EXCLUDED.surface_m2,
      rooms = EXCLUDED.rooms,
      property_type = EXCLUDED.property_type,
      lat = EXCLUDED.lat,
      lon = EXCLUDED.lon,
      source = EXCLUDED.source,
      source_row_id = EXCLUDED.source_row_id
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE sales_transactions")

            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for record in reader:
                    row = parse_row(record, os.path.basename(path))
                    if row is None:
                        skipped += 1
                        continue
                    cur.execute(sql, row.__dict__)
                    inserted += 1

        conn.commit()

    return inserted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Import DVF-like transactions for Paris into PostGIS")
    parser.add_argument("--csv", required=True, help="Path to local DVF-like CSV file")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="Postgres URL")
    parser.add_argument("--truncate", action="store_true", help="Truncate existing rows before import")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required (flag or env)")

    inserted, skipped = import_csv(args.csv, args.database_url, args.truncate)
    print(f"Import finished. Inserted/updated={inserted}, skipped={skipped}")


if __name__ == "__main__":
    main()
