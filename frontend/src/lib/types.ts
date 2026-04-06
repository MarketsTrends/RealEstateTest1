export type PropertyType = 'apartment' | 'house' | 'unknown'
export type DPEClass = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G'

export interface AnalysisRequest {
  property: {
    property_type: PropertyType
    address: string | null
    surface_m2: number | null
    country_code: string
    dpe_class: DPEClass | null
  }
  acquisition: {
    purchase_price_eur: number
    fees_and_works_eur: number
  }
  income: {
    monthly_rent_eur: number
    other_monthly_income_eur: number
    vacancy_rate: number
  }
  expenses: {
    annual_operating_expenses_eur: number
  }
  financing: {
    down_payment_eur: number
    loan_amount_eur: number
    interest_rate_annual: number
    term_years: number
  }
  exit: {
    hold_years: number
    appreciation_rate_annual: number
    sale_cost_rate: number
  }
  valuation: {
    discount_rate_annual_for_npv: number
  }
  model: {
    cashflow_frequency: 'annual'
    debt_compounding: 'monthly'
    rounding: 'cent'
  }
}

export interface AnalysisResponse {
  meta: {
    engine_version: string
    created_at: string
    warnings: string[]
  }
  metrics: {
    noi_annual_eur: number
    cashflow_annual_eur: number
    cashflow_monthly_eur: number
    cap_rate_on_purchase_price: number | null
    cash_on_cash_return: number | null
    dscr: number | null
    break_even_occupancy: number | null
    irr_annual: number | null
    npv_eur: number
    [key: string]: number | string | null
  }
  risk_flags: Array<{
    code: string
    severity: 'info' | 'medium' | 'high'
    message: string
  }>
  pro_forma_yearly: Array<{
    year: number
    gross_rent_annual_eur: number
    effective_rent_annual_eur: number
    operating_expenses_annual_eur: number
    noi_annual_eur: number
    debt_service_annual_eur: number
    cashflow_annual_eur: number
    loan_balance_end_eur: number
    property_value_end_eur: number
    equity_end_eur: number
  }>
  scenarios: Record<
    'base' | 'optimistic' | 'prudent',
    {
      deltas: Record<string, number>
      metrics: AnalysisResponse['metrics']
    }
  >
}

export interface ApiError {
  detail?: string | Array<{ msg?: string }>
}
