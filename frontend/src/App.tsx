import { useMemo, useState } from 'react'

import { CompsSection } from './components/CompsSection'
import { DealForm } from './components/DealForm'
import { ResultsView } from './components/ResultsView'
import { downloadPdfReport, getCompsSales, postAnalysis } from './lib/api'
import type { AnalysisRequest, AnalysisResponse, CompsResponse } from './lib/types'

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

export default function App(): JSX.Element {
  const [form, setForm] = useState<AnalysisRequest>(sampleDeal)
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [comps, setComps] = useState<CompsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [compsLoading, setCompsLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [compsError, setCompsError] = useState<string | null>(null)

  const assumptions = useMemo(
    () => [
      'Analysis is pre-tax.',
      'Yearly projections assume flat operating assumptions unless scenarios adjust inputs.'
    ],
    []
  )

  const submit = async (): Promise<void> => {
    try {
      setLoading(true)
      setError(null)
      setCompsError(null)

      const data = await postAnalysis(form)
      setResult(data)

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

  return (
    <main className="container">
      <h1>Deal Analysis</h1>
      <p className="subtitle">Minimal MVP UI for instant real-estate analysis.</p>

      <div className="actions">
        <button type="button" onClick={exportPdf} disabled={exporting}>
          {exporting ? 'Exporting PDF…' : 'Export PDF'}
        </button>
      </div>

      <div className="layout">
        <DealForm form={form} onChange={setForm} onSubmit={submit} loading={loading} onLoadSample={() => setForm(sampleDeal)} />
        <ResultsView result={result} />
      </div>

      <CompsSection
        comps={comps}
        loading={compsLoading}
        error={compsError}
        hasCoordinates={form.property.lat !== null && form.property.lon !== null}
      />

      {error && <div className="error">{error}</div>}

      <section className="assumptions">
        <h3>Assumptions</h3>
        <ul>
          {assumptions.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </main>
  )
}
