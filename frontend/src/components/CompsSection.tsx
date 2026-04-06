import type { CompsResponse } from '../lib/types'

interface Props {
  comps: CompsResponse | null
  loading: boolean
  error: string | null
  hasCoordinates: boolean
}

const currency = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 })

function money(v: number | null): string {
  if (v === null) return '—'
  return currency.format(v)
}

export function CompsSection({ comps, loading, error, hasCoordinates }: Props): JSX.Element {
  if (!hasCoordinates) {
    return <section className="panel"><h2>Sales comps</h2><p>Provide lat/lon to fetch comps.</p></section>
  }

  if (loading) {
    return <section className="panel"><h2>Sales comps</h2><p>Loading comps…</p></section>
  }

  if (error) {
    return <section className="panel"><h2>Sales comps</h2><p className="error-inline">{error}</p></section>
  }

  if (!comps) {
    return <section className="panel"><h2>Sales comps</h2><p>Run analysis to load comps.</p></section>
  }

  return (
    <section className="panel">
      <h2>Sales comps</h2>
      <p>Status: {comps.available ? 'available' : 'unavailable'}</p>
      {comps.warnings.length > 0 && <p>{comps.warnings.join(' · ')}</p>}

      <div className="kpi-grid">
        <div className="kpi-card"><span>Comps count</span><strong>{comps.stats.n}</strong></div>
        <div className="kpi-card"><span>Median €/m²</span><strong>{money(comps.stats.median_price_per_sqm_eur)}</strong></div>
        <div className="kpi-card"><span>Quartile range €/m²</span><strong>{money(comps.stats.p25_price_per_sqm_eur)} - {money(comps.stats.p75_price_per_sqm_eur)}</strong></div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Price</th>
            <th>Surface</th>
            <th>Rooms</th>
            <th>Type</th>
            <th>Distance (m)</th>
          </tr>
        </thead>
        <tbody>
          {comps.comps.slice(0, 12).map((c) => (
            <tr key={c.transaction_id}>
              <td>{c.sold_at}</td>
              <td>{money(c.price_eur)}</td>
              <td>{c.surface_m2 ?? '—'}</td>
              <td>{c.rooms ?? '—'}</td>
              <td>{c.property_type}</td>
              <td>{c.distance_m.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
