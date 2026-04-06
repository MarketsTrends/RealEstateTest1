import type { AnalysisResponse } from '../lib/types'

interface Props {
  result: AnalysisResponse | null
}

const currency = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 })
const pct = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 2 })

function fmtMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return currency.format(value)
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return pct.format(value)
}

export function ResultsView({ result }: Props): JSX.Element {
  if (!result) {
    return (
      <section className="panel">
        <h2>Results</h2>
        <p>Run analysis to view core KPIs, risk flags, scenarios, and yearly projections.</p>
      </section>
    )
  }

  const { metrics } = result

  return (
    <section className="panel">
      <h2>Results</h2>

      <div className="kpi-grid">
        <Kpi label="NOI" value={fmtMoney(metrics.noi_annual_eur)} />
        <Kpi label="Annual cash flow" value={fmtMoney(metrics.cashflow_annual_eur)} />
        <Kpi label="Monthly cash flow" value={fmtMoney(metrics.cashflow_monthly_eur)} />
        <Kpi label="Cap rate" value={fmtPct(metrics.cap_rate_on_purchase_price)} />
        <Kpi label="Cash-on-cash" value={fmtPct(metrics.cash_on_cash_return)} />
        <Kpi label="DSCR" value={metrics.dscr?.toFixed(2) ?? '—'} />
        <Kpi label="Break-even occupancy" value={fmtPct(metrics.break_even_occupancy)} />
        <Kpi label="IRR" value={fmtPct(metrics.irr_annual)} />
        <Kpi label="NPV" value={fmtMoney(metrics.npv_eur)} />
      </div>

      <h3>Risk flags</h3>
      {result.risk_flags.length === 0 ? (
        <p>No risk flags.</p>
      ) : (
        <ul>
          {result.risk_flags.map((flag) => (
            <li key={flag.code}><strong>{flag.severity.toUpperCase()}</strong> — {flag.message}</li>
          ))}
        </ul>
      )}

      <h3>Scenarios</h3>
      <table>
        <thead>
          <tr>
            <th>Scenario</th>
            <th>NOI</th>
            <th>Cash flow</th>
            <th>Cap rate</th>
            <th>IRR</th>
          </tr>
        </thead>
        <tbody>
          {(['base', 'optimistic', 'prudent'] as const).map((name) => (
            <tr key={name}>
              <td>{name}</td>
              <td>{fmtMoney(result.scenarios[name].metrics.noi_annual_eur as number)}</td>
              <td>{fmtMoney(result.scenarios[name].metrics.cashflow_annual_eur as number)}</td>
              <td>{fmtPct(result.scenarios[name].metrics.cap_rate_on_purchase_price as number | null)}</td>
              <td>{fmtPct(result.scenarios[name].metrics.irr_annual as number | null)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Yearly pro forma</h3>
      <table>
        <thead>
          <tr>
            <th>Year</th>
            <th>NOI</th>
            <th>Debt service</th>
            <th>Cash flow</th>
            <th>Loan balance end</th>
            <th>Equity end</th>
          </tr>
        </thead>
        <tbody>
          {result.pro_forma_yearly.map((row) => (
            <tr key={row.year}>
              <td>{row.year}</td>
              <td>{fmtMoney(row.noi_annual_eur)}</td>
              <td>{fmtMoney(row.debt_service_annual_eur)}</td>
              <td>{fmtMoney(row.cashflow_annual_eur)}</td>
              <td>{fmtMoney(row.loan_balance_end_eur)}</td>
              <td>{fmtMoney(row.equity_end_eur)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Kpi({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
