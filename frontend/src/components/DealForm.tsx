import { useState } from 'react'

import type { AnalysisRequest, DPEClass, PropertyType } from '../lib/types'

interface Props {
  form: AnalysisRequest
  loading: boolean
  onChange: (next: AnalysisRequest) => void
  onSubmit: () => void
  onLoadSample: () => void
}

function num(v: string): number {
  const parsed = Number(v)
  return Number.isFinite(parsed) ? parsed : 0
}

function percentDisplay(value: number): string {
  return String(Number((value * 100).toFixed(3)))
}

export function DealForm({ form, loading, onChange, onSubmit, onLoadSample }: Props): JSX.Element {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const update = (path: string, value: string): void => {
    const next: AnalysisRequest = structuredClone(form)
    const [root, key] = path.split('.')
    const target = (next as unknown as Record<string, Record<string, unknown>>)[root]

    if (key === 'address') {
      target[key] = value.trim() ? value : null
    } else if (key === 'property_type') {
      target[key] = value as PropertyType
    } else if (key === 'dpe_class') {
      target[key] = value ? (value as DPEClass) : null
    } else if (key === 'country_code') {
      target[key] = value
    } else if (key === 'surface_m2' || key === 'lat' || key === 'lon') {
      target[key] = value.trim() ? num(value) : null
    } else {
      target[key] = num(value)
    }

    onChange(next)
  }

  const updatePercent = (path: string, value: string): void => {
    const next: AnalysisRequest = structuredClone(form)
    const [root, key] = path.split('.')
    const target = (next as unknown as Record<string, Record<string, unknown>>)[root]
    target[key] = value.trim() ? num(value) / 100 : 0
    onChange(next)
  }

  return (
    <section className="panel form-shell">
      <div className="panel-header">
        <div>
          <h2>Deal inputs</h2>
          <p className="muted">Structured by underwriting logic, not by backend object shape.</p>
        </div>
        <button type="button" className="button-secondary" onClick={onLoadSample}>Load demo</button>
      </div>

      <div className="section-stack">
        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Property</h3>
              <p className="muted">Location and asset characteristics.</p>
            </div>
            <span className="section-summary">
              {form.property.property_type} {form.property.surface_m2 ? `· ${form.property.surface_m2} m²` : ''}
            </span>
          </div>

          <div className="field-grid">
            <label>
              Property type
              <select value={form.property.property_type} onChange={(e) => update('property.property_type', e.target.value)}>
                <option value="apartment">apartment</option>
                <option value="house">house</option>
                <option value="unknown">unknown</option>
              </select>
            </label>

            <label>
              Address
              <input
                placeholder="e.g. Paris 11e"
                value={form.property.address ?? ''}
                onChange={(e) => update('property.address', e.target.value)}
              />
            </label>

            <label>
              Surface m²
              <input
                type="number"
                value={form.property.surface_m2 ?? ''}
                onChange={(e) => update('property.surface_m2', e.target.value)}
              />
            </label>

            <label>
              DPE class
              <select value={form.property.dpe_class ?? ''} onChange={(e) => update('property.dpe_class', e.target.value)}>
                <option value="">—</option>
                {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((dpe) => (
                  <option key={dpe} value={dpe}>{dpe}</option>
                ))}
              </select>
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Purchase</h3>
              <p className="muted">Entry valuation and upfront costs.</p>
            </div>
            <span className="section-summary">
              {(form.acquisition.purchase_price_eur + form.acquisition.fees_and_works_eur).toLocaleString('fr-FR')} €
            </span>
          </div>

          <div className="field-grid">
            <label>
              Purchase price (€)
              <input
                type="number"
                value={form.acquisition.purchase_price_eur}
                onChange={(e) => update('acquisition.purchase_price_eur', e.target.value)}
              />
            </label>

            <label>
              Fees & works (€)
              <input
                type="number"
                value={form.acquisition.fees_and_works_eur}
                onChange={(e) => update('acquisition.fees_and_works_eur', e.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Income</h3>
              <p className="muted">Revenue assumptions before operating costs.</p>
            </div>
            <span className="section-summary">
              {((form.income.monthly_rent_eur + form.income.other_monthly_income_eur) * 12).toLocaleString('fr-FR')} €/year
            </span>
          </div>

          <div className="field-grid">
            <label>
              Monthly rent (€)
              <input
                type="number"
                value={form.income.monthly_rent_eur}
                onChange={(e) => update('income.monthly_rent_eur', e.target.value)}
              />
            </label>

            <label>
              Other monthly income (€)
              <input
                type="number"
                value={form.income.other_monthly_income_eur}
                onChange={(e) => update('income.other_monthly_income_eur', e.target.value)}
              />
            </label>

            <label>
              Vacancy rate (%)
              <input
                type="number"
                step="0.1"
                value={percentDisplay(form.income.vacancy_rate)}
                onChange={(e) => updatePercent('income.vacancy_rate', e.target.value)}
              />
              <small className="helper-text">Enter 5 for 5%.</small>
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Costs</h3>
              <p className="muted">Operating expenses only, excluding debt service.</p>
            </div>
            <span className="section-summary">
              {form.expenses.annual_operating_expenses_eur.toLocaleString('fr-FR')} €/year
            </span>
          </div>

          <div className="field-grid">
            <label>
              Annual operating expenses (€)
              <input
                type="number"
                value={form.expenses.annual_operating_expenses_eur}
                onChange={(e) => update('expenses.annual_operating_expenses_eur', e.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Financing</h3>
              <p className="muted">Leverage, cost of debt, and duration.</p>
            </div>
            <span className="section-summary">
              {form.financing.loan_amount_eur.toLocaleString('fr-FR')} € loan
            </span>
          </div>

          <div className="field-grid">
            <label>
              Down payment (€)
              <input
                type="number"
                value={form.financing.down_payment_eur}
                onChange={(e) => update('financing.down_payment_eur', e.target.value)}
              />
            </label>

            <label>
              Loan amount (€)
              <input
                type="number"
                value={form.financing.loan_amount_eur}
                onChange={(e) => update('financing.loan_amount_eur', e.target.value)}
              />
            </label>

            <label>
              Interest rate (%)
              <input
                type="number"
                step="0.01"
                value={percentDisplay(form.financing.interest_rate_annual)}
                onChange={(e) => updatePercent('financing.interest_rate_annual', e.target.value)}
              />
              <small className="helper-text">Enter 3.2 for 3.2%.</small>
            </label>

            <label>
              Term (years)
              <input
                type="number"
                value={form.financing.term_years}
                onChange={(e) => update('financing.term_years', e.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Exit assumptions</h3>
              <p className="muted">Hold duration, appreciation, and sale friction.</p>
            </div>
            <span className="section-summary">
              {form.exit.hold_years} years hold
            </span>
          </div>

          <div className="field-grid">
            <label>
              Hold years
              <input
                type="number"
                value={form.exit.hold_years}
                onChange={(e) => update('exit.hold_years', e.target.value)}
              />
            </label>

            <label>
              Annual appreciation (%)
              <input
                type="number"
                step="0.1"
                value={percentDisplay(form.exit.appreciation_rate_annual)}
                onChange={(e) => updatePercent('exit.appreciation_rate_annual', e.target.value)}
              />
            </label>

            <label>
              Exit sale costs (%)
              <input
                type="number"
                step="0.1"
                value={percentDisplay(form.exit.sale_cost_rate)}
                onChange={(e) => updatePercent('exit.sale_cost_rate', e.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Valuation</h3>
              <p className="muted">Discount rate for NPV only.</p>
            </div>
            <span className="section-summary">NPV input</span>
          </div>

          <div className="field-grid">
            <label>
              Discount rate (%)
              <input
                type="number"
                step="0.1"
                value={percentDisplay(form.valuation.discount_rate_annual_for_npv)}
                onChange={(e) => updatePercent('valuation.discount_rate_annual_for_npv', e.target.value)}
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <div className="form-section-header">
            <div>
              <h3>Advanced data</h3>
              <p className="muted">Optional inputs for comps and geo-aware workflows.</p>
            </div>
            <button
              type="button"
              className="button-ghost"
              onClick={() => setShowAdvanced((prev) => !prev)}
            >
              {showAdvanced ? 'Hide' : 'Show'}
            </button>
          </div>

          {showAdvanced && (
            <div className="field-grid">
              <label>
                Country code
                <input
                  value={form.property.country_code}
                  onChange={(e) => update('property.country_code', e.target.value)}
                />
              </label>

              <label>
                Latitude
                <input
                  type="number"
                  step="0.000001"
                  placeholder="48.8592"
                  value={form.property.lat ?? ''}
                  onChange={(e) => update('property.lat', e.target.value)}
                />
                <small className="helper-text">Used for comps lookup with longitude.</small>
              </label>

              <label>
                Longitude
                <input
                  type="number"
                  step="0.000001"
                  placeholder="2.3784"
                  value={form.property.lon ?? ''}
                  onChange={(e) => update('property.lon', e.target.value)}
                />
                <small className="helper-text">If missing, comps stay unavailable.</small>
              </label>
            </div>
          )}
        </section>
      </div>

      <div className="form-submit-row">
        <button type="button" className="primary-button submit" onClick={onSubmit} disabled={loading}>
          {loading ? 'Analyzing…' : 'Run analysis'}
        </button>
      </div>
    </section>
  )
}
