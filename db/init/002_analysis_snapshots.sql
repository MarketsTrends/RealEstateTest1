CREATE TABLE IF NOT EXISTS analysis_snapshots (
  id UUID PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  title TEXT,
  address_label TEXT,
  app_version TEXT,
  engine_version TEXT,
  request_payload_json JSONB NOT NULL,
  analysis_response_json JSONB NOT NULL,
  comps_response_json JSONB,
  memo_response_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_created_at_desc
  ON analysis_snapshots (created_at DESC);
