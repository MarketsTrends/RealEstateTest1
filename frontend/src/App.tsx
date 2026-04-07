import { useEffect, useState } from 'react'

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
const number = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })

function money(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return euro.format(value)
}

function ratio(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return pct.format(value)
}

function eurPerSqm(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${number.format(value)} €/m²`
}

function parseSnapshotIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/analysis\/([^/]+)$/)
  return match ? decodeURIComponent(match[1]) : null
}

function parseCompareIds(pathname: string, search: string): string[] | null {
  if (pathname !== '/compare') return null
  const raw = new URLSearchParams(search).get('ids')
  if (!raw) return []
  return raw
    .split(',')
    .map((id) => id.trim())
    .filter(Boolean)
}

function buildCompareUrl(ids: string[]): string {
  return `/compare?ids=${ids.join(',')}`
}

function investmentTone(view: SnapshotSummary['investment_view'] | MemoResponse['investment_view'] | null): 'good' | 'warn' | 'info' | 'neutral' {
  if (view === 'strong') return 'good'
  if (view === 'balanced') return 'info'
  if (view === 'cautious') return 'warn'
  if (view === 'weak') return 'warn'
  return 'neutral'
}

function humanizePropertyType(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

type WorkspaceTab = 'overview' | 'memo' | 'comps' | 'library'

export default function App(): JSX.Element {
  const compareIds = parseCompareIds(window.location.pathname, window.location.search)
  if (compareIds !== null) {
    return <ComparePage ids={compareIds} />
  }

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
  const [recentError, setRecentError] = useState<string | null>(null)
  const [dirty, setDirty] = useState(false)
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle')
  const [selectedCompareIds, setSelectedCompareIds] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('overview')

  const refreshRecent = async (): Promise<void> => {
    try {
      const data = await getRecentAnalyses(10)
      setRecentSnapshots(data)
      setRecentError(null)
      setSelectedCompareIds((prev) => prev.filter((id) => data.some((s) => s.id === id)))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Recent analyses unavailable'
      setRecentSnapshots([])
      setRecentError(message)
      setSelectedCompareIds([])
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
    setActiveTab('overview')
  }

  const toggleCompare = (snapshotId: string): void => {
    setSelectedCompareIds((prev) => {
      if (prev.includes(snapshotId)) {
        return prev.filter((id) => id !== snapshotId)
      }
      return [...prev, snapshotId]
    })
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
      setActiveTab('overview')

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
      setResult(null)
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
      setActiveTab('memo')
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
      setActiveTab('library')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setSaveError(message)
      setSavedSnapshot(null)
    } finally {
      setSaving(false)
    }
  }

  const shareLink = savedSnapshot ? `${window.location.origin}/analysis/${savedSnapshot.id}` : null
  const compareDisabled = selectedCompareIds.length < 2 || selectedCompareIds.length > 4
  const dealTitle = form.property.address?.trim() || 'New deal analysis'
  const dealMeta = [
    humanizePropertyType(form.property.property_type),
    form.property.surface_m2 ? `${form.property.surface_m2} m²` : null,
    form.property.dpe_class ? `DPE ${form.property.dpe_class}` : null
  ].filter(Boolean).join(' · ')

  const totalProjectCost = form.acquisition.purchase_price_eur + form.acquisition.fees_and_works_eur
  const annualGrossIncome = (form.income.monthly_rent_eur + form.income.other_monthly_income_eur) * 12
  const ltv = form.acquisition.purchase_price_eur > 0
    ? form.financing.loan_amount_eur / form.acquisition.purchase_price_eur
    : null

  return (
    <main className="container app-shell">
      <section className="page-hero">
        <div>
          <div className="eyebrow">Deterministic underwriting workspace</div>
          <div className="hero-heading-row">
            <h1>{dealTitle}</h1>
            <Badge label="Live analysis" tone="info" />
          </div>
          <p className="subtitle">
            Investor-grade deal analysis for rental underwriting, memo generation, comps, and snapshot comparison.
          </p>
          <p className="hero-meta">{dealMeta || 'Add property context to anchor the investment story.'}</p>
        </div>

        <div className="hero-actions">
          <button type="button" className="button-secondary" onClick={saveSnapshot} disabled={saving || loading || !result || dirty}>
            {saving ? 'Saving…' : 'Save snapshot'}
          </button>
          <button type="button" className="button-secondary" onClick={generateMemo} disabled={memoLoading || !result || dirty}>
            {memoLoading ? 'Generating memo…' : 'Generate memo'}
          </button>
          <button type="button" className="button-secondary" onClick={exportPdf} disabled={exporting || !result || dirty}>
            {exporting ? 'Preparing PDF…' : 'Export PDF'}
          </button>
        </div>
      </section>

      {shareLink && (
        <section className="panel callout callout-success">
          <div className="panel-header">
            <div>
              <h2>Snapshot saved</h2>
              <p className="muted">This analysis is now frozen as a read-only point-in-time view.</p>
            </div>
            <Badge label="Shareable" tone="good" />
          </div>

          <a className="share-link" href={shareLink}>{shareLink}</a>

          <div className="share-actions">
            <button
              type="button"
              className="button-secondary"
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

      {saveError && <div className="callout callout-danger">{saveError}</div>}
      {error && <div className="callout callout-danger">{error}</div>}
      {dirty && <div className="callout callout-warn">Inputs changed. Re-run analysis before exporting, generating a memo, or saving a snapshot.</div>}
      {!result && !dirty && !loading && (
        <div className="callout callout-neutral">
          Start with the left rail, run the underwriting, then review the decision workspace on the right.
        </div>
      )}

      <div className="workspace-layout">
        <aside className="workspace-aside">
          <div className="sticky-stack">
            <section className="panel context-panel">
              <div className="panel-header">
                <div>
                  <h2>Deal context</h2>
                  <p className="muted">A quick read before underwriting.</p>
                </div>
                <Badge label="Live inputs" />
              </div>

              <div className="context-grid">
                <MiniStat label="Total project cost" value={money(totalProjectCost)} />
                <MiniStat label="Gross annual income" value={money(annualGrossIncome)} />
                <MiniStat label="Loan-to-value" value={ltv === null ? '—' : ratio(ltv)} />
                <MiniStat label="Hold period" value={`${form.exit.hold_years} years`} />
              </div>
            </section>

            <DealForm
              form={form}
              onChange={updateForm}
              onSubmit={submit}
              loading={loading}
              onLoadSample={() => updateForm(sampleDeal)}
            />
          </div>
        </aside>

        <section className="workspace-main">
          <div className="tab-strip">
            <button
              type="button"
              className={`tab-button ${activeTab === 'overview' ? 'tab-button-active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              type="button"
              className={`tab-button ${activeTab === 'memo' ? 'tab-button-active' : ''}`}
              onClick={() => setActiveTab('memo')}
            >
              Memo
            </button>
            <button
              type="button"
              className={`tab-button ${activeTab === 'comps' ? 'tab-button-active' : ''}`}
              onClick={() => setActiveTab('comps')}
            >
              Comps
            </button>
            <button
              type="button"
              className={`tab-button ${activeTab === 'library' ? 'tab-button-active' : ''}`}
              onClick={() => setActiveTab('library')}
            >
              Library
            </button>
          </div>

          {activeTab === 'overview' && <ResultsView result={result} />}

          {activeTab === 'memo' && (
            <MemoSection
              memo={memo}
              loading={memoLoading}
              error={memoError}
              emptyMessage="Generate a memo after running analysis. The memo explains the deterministic output but does not recalculate it."
            />
          )}

          {activeTab === 'comps' && (
            <CompsSection
              comps={comps}
              loading={compsLoading}
              error={compsError}
              hasCoordinates={form.property.lat !== null && form.property.lon !== null}
              noCoordinatesMessage="Add latitude and longitude in Advanced data to enable Paris sales comps."
              emptyMessage="Comps load automatically after analysis when coordinates are present."
            />
          )}

          {activeTab === 'library' && (
            <RecentSnapshotsPanel
              recentSnapshots={recentSnapshots}
              recentError={recentError}
              selectedCompareIds={selectedCompareIds}
              onToggleCompare={toggleCompare}
              onClearSelection={() => setSelectedCompareIds([])}
              compareDisabled={compareDisabled}
            />
          )}
        </section>
      </div>
    </main>
  )
}

function MiniStat({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function RecentSnapshotsPanel({
  recentSnapshots,
  recentError,
  selectedCompareIds,
  onToggleCompare,
  onClearSelection,
  compareDisabled
}: {
  recentSnapshots: SnapshotSummary[]
  recentError: string | null
  selectedCompareIds: string[]
  onToggleCompare: (snapshotId: string) => void
  onClearSelection: () => void
  compareDisabled: boolean
}): JSX.Element {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Snapshot library</h2>
          <p className="muted">Saved point-in-time analyses for sharing and comparison.</p>
        </div>
        <Badge label="2 to 4 for compare" />
      </div>

      {recentError && (
        <div className="callout callout-neutral inline-callout">
          Snapshot library is unavailable locally right now. Core analysis still works.
        </div>
      )}

      <div className="compare-toolbar">
        <span className="muted">
          {selectedCompareIds.length}/4 selected
        </span>
        <div className="share-actions">
          <a className={`button-link ${compareDisabled ? 'button-link-disabled' : ''}`} href={buildCompareUrl(selectedCompareIds)}>
            Compare selected
          </a>
          <button type="button" className="button-secondary" onClick={onClearSelection} disabled={selectedCompareIds.length === 0}>
            Clear
          </button>
        </div>
      </div>

      {selectedCompareIds.length < 2 && (
        <p className="muted">Select at least 2 snapshots to unlock side-by-side comparison.</p>
      )}
      {selectedCompareIds.length > 4 && (
        <p className="error-inline">Select at most 4 deals.</p>
      )}

      {recentSnapshots.length === 0 ? (
        <div className="empty-state">
          <h3>No saved analyses yet</h3>
          <p>Run an analysis, then save a snapshot to start building a deal library.</p>
        </div>
      ) : (
        <ul className="recent-list">
          {recentSnapshots.map((item) => (
            <li key={item.id} className="recent-item">
              <div className="recent-main">
                <label className="compare-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedCompareIds.includes(item.id)}
                    onChange={() => onToggleCompare(item.id)}
                    disabled={!selectedCompareIds.includes(item.id) && selectedCompareIds.length >= 4}
                  />
                  Compare
                </label>

                <div className="recent-text">
                  <a href={`/analysis/${item.id}`}><strong>{item.title}</strong></a>
                  <p className="muted">
                    {item.address_label ?? 'No address'} · {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="recent-badges">
                {item.investment_view ? <Badge label={item.investment_view} tone={investmentTone(item.investment_view)} /> : null}
                {item.has_memo ? <Badge label="memo" /> : null}
                {item.has_comps ? <Badge label="comps" /> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
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
    return <main className="container"><div className="callout callout-danger">{error}</div></main>
  }

  if (!snapshot) {
    return <main className="container"><div className="callout callout-danger">Snapshot not found.</div></main>
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
              {snapshot.investment_view ? <Badge label={snapshot.investment_view} tone={investmentTone(snapshot.investment_view)} /> : null}
            </div>
            <p className="subtitle">{snapshot.address_label ?? 'No address label'}</p>
          </div>
          <div className="share-actions">
            <button
              type="button"
              className="button-secondary"
              onClick={() => {
                if (!navigator.clipboard) return
                void navigator.clipboard.writeText(shareLink)
                setCopyStatus('copied')
              }}
            >
              {copyStatus === 'copied' ? 'Link copied' : 'Copy link'}
            </button>
          </div>
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
          <KpiItem label="Median €/m² comps" value={eurPerSqm(snapshot.comps?.stats.median_price_per_sqm_eur ?? null)} />
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

type MetricRule = {
  key: string
  label: string
  prefer: 'high' | 'low'
  format: (value: number | null | undefined) => string
  get: (snapshot: SnapshotResponse) => number | null | undefined
}

const metricRules: MetricRule[] = [
  { key: 'noi', label: 'NOI', prefer: 'high', format: money, get: (s) => s.analysis.metrics.noi_annual_eur },
  { key: 'cashflow_year', label: 'Annual cash flow', prefer: 'high', format: money, get: (s) => s.analysis.metrics.cashflow_annual_eur },
  { key: 'cashflow_month', label: 'Monthly cash flow', prefer: 'high', format: money, get: (s) => s.analysis.metrics.cashflow_monthly_eur },
  { key: 'irr', label: 'IRR', prefer: 'high', format: ratio, get: (s) => s.analysis.metrics.irr_annual },
  { key: 'npv', label: 'NPV', prefer: 'high', format: money, get: (s) => s.analysis.metrics.npv_eur },
  { key: 'cap_rate', label: 'Cap rate', prefer: 'high', format: ratio, get: (s) => s.analysis.metrics.cap_rate_on_purchase_price },
  { key: 'coc', label: 'Cash-on-cash', prefer: 'high', format: ratio, get: (s) => s.analysis.metrics.cash_on_cash_return },
  {
    key: 'dscr',
    label: 'DSCR',
    prefer: 'high',
    format: (v) => (v === null || v === undefined ? '—' : v.toFixed(2)),
    get: (s) => s.analysis.metrics.dscr
  },
  { key: 'be_occ', label: 'Break-even occupancy', prefer: 'low', format: ratio, get: (s) => s.analysis.metrics.break_even_occupancy }
]

function ComparePage({ ids }: { ids: string[] }): JSX.Element {
  const [snapshots, setSnapshots] = useState<SnapshotResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (ids.length < 2 || ids.length > 4) return

    const load = async (): Promise<void> => {
      try {
        setLoading(true)
        setError(null)
        const data = await Promise.all(ids.map((id) => getAnalysisSnapshot(id)))
        setSnapshots(data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load snapshots for compare'
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [ids])

  if (ids.length < 2) {
    return <main className="container"><section className="panel"><h1>Compare deals</h1><p>Select 2 to 4 saved snapshots from the library.</p><p><a href="/">Back to analyses</a></p></section></main>
  }

  if (ids.length > 4) {
    return <main className="container"><section className="panel"><h1>Compare deals</h1><p>You can compare at most 4 snapshots at once.</p><p><a href="/">Back to analyses</a></p></section></main>
  }

  if (loading) {
    return <main className="container"><p>Loading comparison…</p></main>
  }

  if (error) {
    return <main className="container"><div className="callout callout-danger">{error}</div></main>
  }

  return (
    <main className="container">
      <p><a href="/">← Back to analyses</a></p>

      <section className="panel">
        <div className="panel-header">
          <h1>Compare deals</h1>
          <Badge label={`Compare mode · ${snapshots.length} selected`} tone="info" />
        </div>
        <p className="muted">Comparison uses saved snapshot data only. No recalculation is performed here.</p>

        <div className="compare-chip-row">
          {snapshots.map((s) => {
            const remaining = snapshots.filter((x) => x.id !== s.id).map((x) => x.id)
            return (
              <div key={s.id} className="compare-chip">
                <strong>{s.title}</strong>
                <p className="muted">{new Date(s.created_at).toLocaleDateString()}</p>
                <a href={buildCompareUrl(remaining)}>Remove</a>
              </div>
            )
          })}
        </div>
      </section>

      <section className="panel compare-grid-header">
        {snapshots.map((s) => (
          <div key={s.id} className="compare-deal-card">
            <h3>{s.title}</h3>
            <p className="muted">{s.address_label ?? 'No address label'}</p>
            <p className="muted">{s.request.property.property_type} · {s.request.property.surface_m2 ?? '—'} m² · DPE {s.request.property.dpe_class ?? '—'}</p>
            <div className="recent-badges">
              {s.investment_view ? <Badge label={s.investment_view} tone={investmentTone(s.investment_view)} /> : <Badge label="no memo view" />}
            </div>
          </div>
        ))}
      </section>

      <section className="panel">
        <h2>Core metrics</h2>
        <div className="compare-table-wrap">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Metric</th>
                {snapshots.map((s) => <th key={s.id}>{s.title}</th>)}
              </tr>
            </thead>
            <tbody>
              {metricRules.map((rule) => {
                const values = snapshots.map((s) => rule.get(s))
                const numericValues = values.filter((v): v is number => typeof v === 'number')
                const best = numericValues.length > 0 ? (rule.prefer === 'high' ? Math.max(...numericValues) : Math.min(...numericValues)) : null
                const worst = numericValues.length > 0 ? (rule.prefer === 'high' ? Math.min(...numericValues) : Math.max(...numericValues)) : null

                return (
                  <tr key={rule.key}>
                    <td>{rule.label}</td>
                    {values.map((value, idx) => {
                      const isBest = typeof value === 'number' && best !== null && value === best && best !== worst
                      const isWorst = typeof value === 'number' && worst !== null && value === worst && best !== worst
                      return (
                        <td key={`${rule.key}-${snapshots[idx].id}`} className={isBest ? 'compare-best' : isWorst ? 'compare-worst' : ''}>
                          {rule.format(value)}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel compare-grid-header">
        {snapshots.map((s) => (
          <div key={`${s.id}-risks`} className="compare-deal-card">
            <h3>Risk & memo — {s.title}</h3>
            <h4>Risk flags</h4>
            {s.analysis.risk_flags.length === 0 ? <p className="muted">No risk flags.</p> : (
              <ul>
                {s.analysis.risk_flags.slice(0, 3).map((r) => <li key={r.code}>{r.severity}: {r.message}</li>)}
              </ul>
            )}
            <h4>Memo highlights</h4>
            {s.memo ? (
              <>
                <p><strong>View:</strong> {s.memo.investment_view}</p>
                <ul>
                  {s.memo.key_risks.slice(0, 2).map((r) => <li key={r}>{r}</li>)}
                </ul>
              </>
            ) : <p className="muted">No memo saved.</p>}
          </div>
        ))}
      </section>

      <section className="panel compare-grid-header">
        {snapshots.map((s) => (
          <div key={`${s.id}-comps`} className="compare-deal-card">
            <h3>Comps — {s.title}</h3>
            {s.comps ? (
              <ul>
                <li>Count: {s.comps.stats.n}</li>
                <li>Median €/m²: {eurPerSqm(s.comps.stats.median_price_per_sqm_eur)}</li>
                <li>Quartile range: {eurPerSqm(s.comps.stats.p25_price_per_sqm_eur)} – {eurPerSqm(s.comps.stats.p75_price_per_sqm_eur)}</li>
              </ul>
            ) : <p className="muted">No comps snapshot saved.</p>}
          </div>
        ))}
      </section>
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
