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

export function DealForm({ form, loading, onChange, onSubmit, onLoadSample }: Props): JSX.Element {
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

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Deal inputs</h2>
        <button type="button" onClick={onLoadSample}>Load demo deal</button>
      </div>
      <p className="muted">Fill key assumptions below. Percentage-like fields use decimals (5% = 0.05).</p>

      <div className="grid">
        <label>Property type
          <select value={form.property.property_type} onChange={(e) => update('property.property_type', e.target.value)}>
            <option value="apartment">apartment</option>
            <option value="house">house</option>
            <option value="unknown">unknown</option>
          </select>
        </label>

        <label>Address (optional)
          <input placeholder="e.g. Paris 11e" value={form.property.address ?? ''} onChange={(e) => update('property.address', e.target.value)} />
        </label>

        <label>Surface m² (optional)
          <input type="number" value={form.property.surface_m2 ?? ''} onChange={(e) => update('property.surface_m2', e.target.value)} />
        </label>

        <label>Latitude (optional)
          <input type="number" step="0.000001" placeholder="48.8592" value={form.property.lat ?? ''} onChange={(e) => update('property.lat', e.target.value)} />
          <small className="helper-text">Used for comps lookup with longitude.</small>
        </label>

        <label>Longitude (optional)
          <input type="number" step="0.000001" placeholder="2.3784" value={form.property.lon ?? ''} onChange={(e) => update('property.lon', e.target.value)} />
          <small className="helper-text">If missing, comps stay unavailable.</small>
        </label>

        <label>DPE class (optional)
          <select value={form.property.dpe_class ?? ''} onChange={(e) => update('property.dpe_class', e.target.value)}>
            <option value="">--</option>
            {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((dpe) => (
              <option key={dpe} value={dpe}>{dpe}</option>
            ))}
          </select>
        </label>

        <label>Purchase price (€)
          <input type="number" value={form.acquisition.purchase_price_eur} onChange={(e) => update('acquisition.purchase_price_eur', e.target.value)} />
        </label>

        <label>Fees & works (€)
          <input type="number" value={form.acquisition.fees_and_works_eur} onChange={(e) => update('acquisition.fees_and_works_eur', e.target.value)} />
        </label>

        <label>Monthly rent (€)
          <input type="number" value={form.income.monthly_rent_eur} onChange={(e) => update('income.monthly_rent_eur', e.target.value)} />
        </label>

        <label>Other monthly income (€)
          <input type="number" value={form.income.other_monthly_income_eur} onChange={(e) => update('income.other_monthly_income_eur', e.target.value)} />
        </label>

        <label>Vacancy rate (decimal)
          <input type="number" step="0.001" value={form.income.vacancy_rate} onChange={(e) => update('income.vacancy_rate', e.target.value)} />
          <small className="helper-text">Example: 0.05 = 5% annual vacancy.</small>
        </label>

        <label>Annual operating expenses (€)
          <input type="number" value={form.expenses.annual_operating_expenses_eur} onChange={(e) => update('expenses.annual_operating_expenses_eur', e.target.value)} />
        </label>

        <label>Down payment (€)
          <input type="number" value={form.financing.down_payment_eur} onChange={(e) => update('financing.down_payment_eur', e.target.value)} />
        </label>

        <label>Loan amount (€)
          <input type="number" value={form.financing.loan_amount_eur} onChange={(e) => update('financing.loan_amount_eur', e.target.value)} />
        </label>

        <label>Interest rate annual (decimal)
          <input type="number" step="0.001" value={form.financing.interest_rate_annual} onChange={(e) => update('financing.interest_rate_annual', e.target.value)} />
          <small className="helper-text">Example: 0.032 = 3.2% annual rate.</small>
        </label>

        <label>Term years
          <input type="number" value={form.financing.term_years} onChange={(e) => update('financing.term_years', e.target.value)} />
        </label>

        <label>Hold years
          <input type="number" value={form.exit.hold_years} onChange={(e) => update('exit.hold_years', e.target.value)} />
        </label>

        <label>Appreciation annual (decimal)
          <input type="number" step="0.001" value={form.exit.appreciation_rate_annual} onChange={(e) => update('exit.appreciation_rate_annual', e.target.value)} />
        </label>

        <label>Sale cost rate (decimal)
          <input type="number" step="0.001" value={form.exit.sale_cost_rate} onChange={(e) => update('exit.sale_cost_rate', e.target.value)} />
          <small className="helper-text">Example: 0.06 = 6% transaction costs on exit.</small>
        </label>
      </div>

      <button type="button" className="submit" onClick={onSubmit} disabled={loading}>
        {loading ? 'Analyzing…' : 'Run analysis'}
      </button>
    </section>
  )
}
