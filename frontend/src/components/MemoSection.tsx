import type { MemoResponse } from '../lib/types'

interface Props {
  memo: MemoResponse | null
  loading: boolean
  error: string | null
  emptyMessage?: string
}

export function MemoSection({ memo, loading, error, emptyMessage }: Props): JSX.Element {
  if (loading) {
    return <section className="panel"><h2>Investment memo</h2><p>Generating memo…</p></section>
  }
  if (error) {
    return <section className="panel"><h2>Investment memo</h2><p className="error-inline">{error}</p></section>
  }
  if (!memo) {
    return <section className="panel"><h2>Investment memo</h2><p>{emptyMessage ?? 'Generate a memo from current deal inputs.'}</p></section>
  }

  return (
    <section className="panel">
      <h2>Investment memo</h2>
      <p><strong>View:</strong> {memo.investment_view}</p>
      <p>{memo.summary}</p>

      <h3>Key strengths</h3>
      <ul>{memo.key_strengths.map((s) => <li key={s}>{s}</li>)}</ul>

      <h3>Key risks</h3>
      <ul>{memo.key_risks.map((s) => <li key={s}>{s}</li>)}</ul>

      <h3>Sensitivity points</h3>
      <ul>{memo.sensitivity_points.map((s) => <li key={s}>{s}</li>)}</ul>

      <h3>Next checks</h3>
      <ul>{memo.next_checks.map((s) => <li key={s}>{s}</li>)}</ul>

      <p className="memo-disclaimer">{memo.disclaimer}</p>
    </section>
  )
}
