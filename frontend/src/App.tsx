import { useEffect, useMemo, useState } from 'react'

import { CompsSection } from './components/CompsSection'
import { DealForm } from './components/DealForm'
import { MemoSection } from './components/MemoSection'
import { ResultsView } from './components/ResultsView'
import {
  downloadPdfReport,
  getAnalysisSnapshot,
  getCompsSales,
  getRecentAnalyses,
  postAnalysis,
  postMemo,
  saveAnalysisSnapshot
} from './lib/api'
import type { AnalysisRequest, AnalysisResponse, CompsResponse, MemoResponse, SnapshotResponse, SnapshotSummary } from './lib/types'

const sampleDeal: AnalysisRequest = {
  property: {
    property_type: 'apartment',
    address: 'Paris 11e',
    lat: 48.8592,
    lon: 2.3784,
    surface_m2: 52,
    country_code: 'FR',
    dpe_class: 'D'
  },
  acquisition: {
    purchase_price_eur: 200000,
    fees_and_works_eur: 15000
  },
  income: {
    monthly_rent_eur: 1350,
    other_monthly_income_eur: 0,
    vacancy_rate: 0.05
  },
  expenses: {
    annual_operating_expenses_eur: 4000
  },
  financing: {
    down_payment_eur: 40000,
    loan_amount_eur: 160000,
    interest_rate_annual: 0.032,
    term_years: 20
  },
  exit: {
    hold_years: 10,
    appreciation_rate_annual: 0.02,
    sale_cost_rate: 0.06
  },
  valuation: {
    discount_rate_annual_for_npv: 0.1
  },
  model: {
    cashflow_frequency: 'annual',
    debt_compounding: 'monthly',
    rounding: 'cent'
  }
}

const euro = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
const pct = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 2 })

function money(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return euro.format(value)
}

function ratio(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return pct.format(value)
}

function parseSnapshotIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/analysis\/([^/]+)$/)
  return match ? decodeURIComponent(match[1]) : null
}

export default function App(): JSX.Element {
  const snapshotIdFromPath = parseSnapshotIdFromPath(window.location.pathname)

  if (snapshotIdFromPath) {
    return <SavedSnapshotPage snapshotId={snapshotIdFromPath} />
  }

  return <LiveAnalysisPage />
}

function Badge({ label, tone = 'neutral' }: { label: string; tone?: 'neutral' | 'good' | 'warn' | 'info' }): JSX.Element {
  return <span className={`badge badge-${tone}`}>{label}</span>
}

function LiveAnalysisPage(): JSX.Element {
  const [form, setForm] = useState<AnalysisRequest>(sampleDeal)
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [comps, setComps] = useState<CompsResponse | null>(null)
  const [memo, setMemo] = useState<MemoResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [compsLoading, setCompsLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [memoLoading, setMemoLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [compsError, setCompsError] = useState<string | null>(null)
  const [memoError, setMemoError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [savedSnapshot, setSavedSnapshot] = useState<SnapshotSummary | null>(null)
  const [recentSnapshots, setRecentSnapshots] = useState<SnapshotSummary[]>([])
  const [dirty, setDirty] = useState(false)
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle')

  const assumptions = useMemo(
    () => [
      'Analysis is pre-tax.',
      'Yearly projections assume flat operating assumptions unless scenarios adjust inputs.'
    ],
    []
  )

  const refreshRecent = async (): Promise<void> => {
    try {
      const data = await getRecentAnalyses(10)
      setRecentSnapshots(data)
    } catch {
      setRecentSnapshots([])
    }
  }

  useEffect(() => {
    void refreshRecent()
  }, [])

  const updateForm = (nextForm: AnalysisRequest): void => {
    setForm(nextForm)
    setDirty(true)
    setResult(null)
    setComps(null)
    setMemo(null)
    setSavedSnapshot(null)
    setCopyStatus('idle')
    setError(null)
    setCompsError(null)
    setMemoError(null)
    setSaveError(null)
  }

  const submit = async (): Promise<void> => {
    try {
      setLoading(true)
      setError(null)
      setCompsError(null)
      setMemoError(null)
      setMemo(null)
      setSavedSnapshot(null)
      setCopyStatus('idle')
      setSaveError(null)

      const data = await postAnalysis(form)
      setResult(data)
      setDirty(false)

      if (form.property.lat !== null && form.property.lon !== null) {
        setCompsLoading(true)
        try {
          const compsData = await getCompsSales({
            lat: form.property.lat,
            lon: form.property.lon,
            property_type: form.property.property_type,
            surface_m2: form.property.surface_m2 ?? undefined
          })
          setComps(compsData)
          setCompsError(null)
        } catch (err) {
          const compsMessage = err instanceof Error ? err.message : 'Comps error'
          setCompsError(compsMessage)
          setComps(null)
        }
      } else {
        setComps(null)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
    } finally {
      setLoading(false)
      setCompsLoading(false)
    }
  }

  const exportPdf = async (): Promise<void> => {
    try {
      setExporting(true)
      setError(null)
      await downloadPdfReport(form)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
    } finally {
      setExporting(false)
    }
  }

  const generateMemo = async (): Promise<void> => {
    try {
      setMemoLoading(true)
      setMemoError(null)
      const data = await postMemo(form)
      setMemo(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setMemoError(message)
      setMemo(null)
    } finally {
      setMemoLoading(false)
    }
  }

  const saveSnapshot = async (): Promise<void> => {
    try {
      setSaving(true)
      setSaveError(null)
      const data = await saveAnalysisSnapshot({
        request: form,
        analysis: result ?? undefined,
        comps,
        memo
      })
      setSavedSnapshot(data)
      await refreshRecent()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setSaveError(message)
      setSavedSnapshot(null)
    } finally {
      setSaving(false)
    }
  }

  const shareLink = savedSnapshot ? `${window.location.origin}/analysis/${savedSnapshot.id}` : null

  return (
    <main className="container">
      <h1>Deal Analysis</h1>
      <p className="subtitle">Minimal MVP UI for instant real-estate analysis.</p>

      <div className="actions">
        <button type="button" onClick={exportPdf} disabled={exporting || !result || dirty}>
          {exporting ? 'Exporting PDF…' : 'Export PDF'}
        </button>
        <button type="button" onClick={generateMemo} disabled={memoLoading || !result || dirty}>
          {memoLoading ? 'Generating memo…' : 'Generate memo'}
        </button>
        <button type="button" onClick={saveSnapshot} disabled={saving || loading || !result || dirty}>
          {saving ? 'Saving…' : 'Save analysis'}
        </button>
      </div>

      {dirty && (
        <div className="error">
          Inputs changed. Re-run analysis to enable Export PDF, Generate memo, and Save analysis.
        </div>
      )}

      {shareLink && (
        <section className="panel share-card">
          <div className="panel-header">
            <h2>Snapshot saved</h2>
            <Badge label="Shareable" tone="info" />
          </div>
          <p>Your snapshot is now a read-only point-in-time link.</p>
          <a className="share-link" href={shareLink}>{shareLink}</a>
          <div className="share-actions">
            <button
              type="button"
              onClick={() => {
                if (!navigator.clipboard) return
                void navigator.clipboard.writeText(shareLink)
                setCopyStatus('copied')
              }}
            >
              {copyStatus === 'copied' ? 'Link copied' : 'Copy link'}
            </button>
            <a className="button-link" href={shareLink}>Open snapshot</a>
          </div>
        </section>
      )}
      {saveError && <div className="error">{saveError}</div>}

      <div className="layout">
        <DealForm form={form} onChange={updateForm} onSubmit={submit} loading={loading} onLoadSample={() => updateForm(sampleDeal)} />
        <ResultsView result={result} />
      </div>

      <MemoSection memo={memo} loading={memoLoading} error={memoError} />

      <CompsSection
        comps={comps}
        loading={compsLoading}
        error={compsError}
        hasCoordinates={form.property.lat !== null && form.property.lon !== null}
      />

      {error && <div className="error">{error}</div>}

      <section className="panel">
        <div className="panel-header">
          <h2>Recent analyses</h2>
          <Badge label="Newest first" />
        </div>
        {recentSnapshots.length === 0 ? (
          <p>No saved analyses yet.</p>
        ) : (
          <ul className="recent-list">
            {recentSnapshots.map((item) => (
              <li key={item.id} className="recent-item">
                <div>
                  <a href={`/analysis/${item.id}`}><strong>{item.title}</strong></a>
                  <p className="muted">{item.address_label ?? 'No address'} · {new Date(item.created_at).toLocaleString()}</p>
                </div>
                <div className="recent-badges">
                  {item.investment_view ? <Badge label={item.investment_view} tone="good" /> : null}
                  {item.has_memo ? <Badge label="memo" /> : null}
                  {item.has_comps ? <Badge label="comps" /> : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="assumptions">
        <h3>Assumptions</h3>
        <ul>
          {assumptions.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </main>
  )
}

function SavedSnapshotPage({ snapshotId }: { snapshotId: string }): JSX.Element {
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle')

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        setLoading(true)
        const data = await getAnalysisSnapshot(snapshotId)
        setSnapshot(data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [snapshotId])

  if (loading) {
    return <main className="container"><p>Loading saved analysis…</p></main>
  }

  if (error) {
    return <main className="container"><div className="error">{error}</div></main>
  }

  if (!snapshot) {
    return <main className="container"><div className="error">Snapshot not found.</div></main>
  }

  const shareLink = `${window.location.origin}/analysis/${snapshot.id}`

  return (
    <main className="container">
      <p><a href="/">← Back to live analysis</a></p>

      <section className="panel snapshot-hero">
        <div className="snapshot-hero-top">
          <div>
            <div className="hero-title-row">
              <h1>{snapshot.title}</h1>
              <Badge label="Saved snapshot" tone="info" />
              {snapshot.investment_view ? <Badge label={snapshot.investment_view} tone="good" /> : null}
            </div>
            <p className="subtitle">{snapshot.address_label ?? 'No address label'}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              if (!navigator.clipboard) return
              void navigator.clipboard.writeText(shareLink)
              setCopyStatus('copied')
            }}
          >
            {copyStatus === 'copied' ? 'Link copied' : 'Copy link'}
          </button>
        </div>

        <div className="snapshot-meta-grid">
          <MetaItem label="Saved at" value={new Date(snapshot.created_at).toLocaleString()} />
          <MetaItem label="Property type" value={snapshot.request.property.property_type} />
          <MetaItem label="Surface" value={snapshot.request.property.surface_m2 ? `${snapshot.request.property.surface_m2} m²` : '—'} />
          <MetaItem label="DPE" value={snapshot.request.property.dpe_class ?? '—'} />
        </div>

        <div className="headline-kpis">
          <KpiItem label="NOI" value={money(snapshot.analysis.metrics.noi_annual_eur)} />
          <KpiItem label="Annual cash flow" value={money(snapshot.analysis.metrics.cashflow_annual_eur)} />
          <KpiItem label="IRR" value={ratio(snapshot.analysis.metrics.irr_annual)} />
          <KpiItem label="DSCR" value={snapshot.analysis.metrics.dscr?.toFixed(2) ?? '—'} />
          <KpiItem label="Median €/m² comps" value={money(snapshot.comps?.stats.median_price_per_sqm_eur ?? null)} />
        </div>
      </section>

      <ResultsView result={snapshot.analysis} />
      <MemoSection memo={snapshot.memo} loading={false} error={null} emptyMessage="No memo was saved for this snapshot." />
      <CompsSection
        comps={snapshot.comps}
        loading={false}
        error={null}
        hasCoordinates={snapshot.request.property.lat !== null && snapshot.request.property.lon !== null}
        noCoordinatesMessage="No coordinates were provided in the saved request."
        emptyMessage="No comps were saved for this snapshot."
      />

      <footer className="snapshot-footer">
        <p>
          Snapshot ID: <code>{snapshot.id}</code> · Engine {snapshot.engine_version} · App {snapshot.app_version}
        </p>
        <p className="muted">This page reflects a saved point-in-time analysis snapshot.</p>
      </footer>
    </main>
  )
}

function MetaItem({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="meta-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function KpiItem({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
