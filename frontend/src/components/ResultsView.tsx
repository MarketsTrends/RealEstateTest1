import type { AnalysisResponse } from '../lib/types'

interface Props {
  result: AnalysisResponse | null
}

const currency = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
const pct = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 2 })

function fmtMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return currency.format(value)
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return pct.format(value)
}

function severityTone(severity: string): 'danger' | 'warn' | 'neutral' {
  if (severity === 'high') return 'danger'
  if (severity === 'medium') return 'warn'
  return 'neutral'
}

function buildVerdict(result: AnalysisResponse): {
  title: string
  tone: 'good' | 'warn' | 'neutral'
  detail: string
} {
  const irr = result.metrics.irr_annual ?? 0
  const cashflow = result.metrics.cashflow_annual_eur ?? 0
  const dscr = result.metrics.dscr ?? 0
  const highRiskCount = result.risk_flags.filter((flag) => flag.severity === 'high').length

  if (highRiskCount > 0 || cashflow < 0 || dscr < 1) {
    return {
      title: 'Needs caution',
      tone: 'warn',
      detail: 'The base case shows at least one material underwriting concern that should be addressed before presenting the deal.'
    }
  }

  if (irr >= 0.12 && cashflow > 0 && dscr >= 1.2) {
    return {
      title: 'Strong base case',
      tone: 'good',
      detail: 'The deal screens well on return, debt coverage, and cash generation under the current deterministic assumptions.'
    }
  }

  return {
    title: 'Balanced but selective',
    tone: 'neutral',
    detail: 'The deal may be viable, but upside and downside need to be weighed carefully through risk flags and scenario spread.'
  }
}

export function ResultsView({ result }: Props): JSX.Element {
  if (!result) {
    return (
      <section className="panel">
        <div className="empty-state empty-state-large">
          <h2>Decision workspace</h2>
          <p>
            Run analysis to surface base-case KPIs, downside flags, scenario spread, and yearly operating profile.
          </p>
        </div>
      </section>
    )
  }

  const { metrics } = result
  const verdict = buildVerdict(result)

  return (
    <div className="results-stack">
      <section className="panel hero-panel">
        <div className="results-hero">
          <div>
            <div className="eyebrow">Decision workspace</div>
            <h2>Base-case underwriting</h2>
            <p className="muted">
              Deterministic output only. Use this section to understand headline attractiveness before opening memo or comps.
            </p>
          </div>

          <div className={`verdict-card verdict-${verdict.tone}`}>
            <span className="verdict-label">Investment read</span>
            <strong>{verdict.title}</strong>
            <p>{verdict.detail}</p>
          </div>
        </div>

        <div className="headline-kpis headline-kpis-wide">
          <Kpi label="IRR" value={fmtPct(metrics.irr_annual)} />
          <Kpi label="Annual cash flow" value={fmtMoney(metrics.cashflow_annual_eur)} />
          <Kpi label="DSCR" value={metrics.dscr?.toFixed(2) ?? '—'} />
          <Kpi label="Cap rate" value={fmtPct(metrics.cap_rate_on_purchase_price)} />
          <Kpi label="Break-even occupancy" value={fmtPct(metrics.break_even_occupancy)} />
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Core metrics</h3>
            <p className="muted">The handful of numbers most likely to anchor an investment decision.</p>
          </div>
        </div>

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
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Risk flags</h3>
            <p className="muted">Read these before moving the deal forward.</p>
          </div>
        </div>

        {result.risk_flags.length === 0 ? (
          <div className="empty-state">
            <h4>No risk flags</h4>
            <p>The rule engine did not surface any issues on the current assumptions.</p>
          </div>
        ) : (
          <div className="risk-grid">
            {result.risk_flags.map((flag) => (
              <article key={flag.code} className={`risk-card risk-card-${severityTone(flag.severity)}`}>
                <div className="risk-card-top">
                  <span className="risk-code">{flag.code}</span>
                  <span className={`risk-severity risk-severity-${severityTone(flag.severity)}`}>
                    {flag.severity}
                  </span>
                </div>
                <p>{flag.message}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Scenario spread</h3>
            <p className="muted">Base, upside, and prudent views to frame the sensitivity of the thesis.</p>
          </div>
        </div>

        <div className="scenario-grid">
          {(['base', 'optimistic', 'prudent'] as const).map((name) => (
            <div key={name} className="scenario-card">
              <div className="scenario-card-top">
                <strong>{name}</strong>
              </div>
              <dl className="scenario-stats">
                <div>
                  <dt>NOI</dt>
                  <dd>{fmtMoney(result.scenarios[name].metrics.noi_annual_eur as number)}</dd>
                </div>
                <div>
                  <dt>Cash flow</dt>
                  <dd>{fmtMoney(result.scenarios[name].metrics.cashflow_annual_eur as number)}</dd>
                </div>
                <div>
                  <dt>Cap rate</dt>
                  <dd>{fmtPct(result.scenarios[name].metrics.cap_rate_on_purchase_price as number | null)}</dd>
                </div>
                <div>
                  <dt>IRR</dt>
                  <dd>{fmtPct(result.scenarios[name].metrics.irr_annual as number | null)}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Yearly pro forma</h3>
            <p className="muted">Operating profile and balance evolution across the hold period.</p>
          </div>
        </div>

        <div className="table-wrap">
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
        </div>
      </section>
    </div>
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
