CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS sales_transactions (
  transaction_id TEXT PRIMARY KEY,
  sold_at DATE NOT NULL,
  price_eur NUMERIC NOT NULL CHECK (price_eur >= 0),
  surface_m2 NUMERIC NULL,
  rooms INTEGER NULL,
  property_type TEXT NOT NULL DEFAULT 'unknown' CHECK (property_type IN ('apartment', 'house', 'unknown')),
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  source TEXT NULL,
  source_row_id TEXT NULL,
  geom GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS (
    ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
  ) STORED
);

CREATE INDEX IF NOT EXISTS idx_sales_transactions_sold_at ON sales_transactions (sold_at);
CREATE INDEX IF NOT EXISTS idx_sales_transactions_property_type ON sales_transactions (property_type);
CREATE INDEX IF NOT EXISTS idx_sales_transactions_surface_m2 ON sales_transactions (surface_m2);
CREATE INDEX IF NOT EXISTS idx_sales_transactions_geom ON sales_transactions USING GIST (geom);
