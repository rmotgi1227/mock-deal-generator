import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDealContext } from '../../context/DealContext'
import GenerationProgress from '../../components/GenerationProgress'
import ErrorMessage from '../../components/ErrorMessage'

const inputStyle = {
  width: '100%', padding: '9px 12px', background: 'var(--surface)',
  border: '1px solid var(--rule)', borderRadius: '6px', color: 'var(--text)',
  fontFamily: 'inherit', fontSize: '14px', outline: 'none',
}
const labelStyle = {
  display: 'block', fontSize: '12px', fontWeight: '500',
  color: 'var(--text-muted)', marginBottom: '6px',
  textTransform: 'uppercase', letterSpacing: '0.06em',
}
const Field = ({ label, children }) => (
  <div><label style={labelStyle}>{label}</label>{children}</div>
)
const focus = (e) => e.target.style.borderColor = 'var(--teal-border)'
const blur = (e) => e.target.style.borderColor = 'var(--rule)'

const INDUSTRIES = [
  'Fintech','Healthcare IT','Cybersecurity','DevTools','HR Tech',
  'Legal Tech','EdTech','Supply Chain','Real Estate Tech','MarTech',
  'InsurTech','Logistics','Manufacturing SaaS','Retail Tech','CleanTech',
]
const DEAL_SIZES = [
  '$25k ARR','$50k ARR','$75k ARR','$100k ARR','$150k ARR',
  '$200k ARR','$300k ARR','$500k ARR','$750k ARR','$1M ARR',
]
const OBJECTIONS = [
  'Security Review','Budget Constraints','Integration Complexity',
  'Compliance Requirements','Vendor Risk Assessment','Contract Negotiation',
  'Technical Fit','ROI Justification','Procurement Process',
  'Competing Priority','Executive Buy-In','Data Privacy',
]

const SeriesPanel = () => {
  const navigate = useNavigate()
  const { seriesGenerateStream, cancelGeneration, loading, error, setError, generationProgress, generationStep } = useDealContext()

  const [form, setForm] = useState({
    account_age_months: 6,
    frequency: 'weekly',
    ae_name: '',
    se_name: '',
    business_use_case: '',
    company_name: '',
    industry: 'Fintech',
    deal_size: '$75k ARR',
    deal_outcome: 'closed_won',
    complexity: 'normal',
    main_objection: 'Security Review',
    buyer_urgency: 'medium',
    starting_sentiment: 'neutral',
    ending_sentiment: 'positive',
    champion_entry: 'after_demo',
  })

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  const onChange = (e) => set(e.target.name, e.target.value)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const payload = {
        ...form,
        account_age_months: Number(form.account_age_months),
        company_name: form.company_name || null,
        ae_name: form.ae_name || null,
        se_name: form.se_name || null,
      }
      const result = await seriesGenerateStream(payload)
      navigate(`/deals/${result.deal_id}`)
    } catch {}
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {error && <ErrorMessage message={error} />}

      {/* Account age + frequency */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label={`Account Age — ${form.account_age_months} month${form.account_age_months !== 1 ? 's' : ''}`}>
          <input type="range" min={1} max={24} value={form.account_age_months}
            onChange={e => set('account_age_months', e.target.value)}
            style={{ width: '100%', marginTop: '6px', accentColor: 'var(--teal)' }} />
        </Field>
        <Field label="Touchpoint Frequency">
          <select name="frequency" value={form.frequency} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="biweekly">Biweekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </Field>
      </div>

      {/* Business use case — full width, required */}
      <Field label="Business Use Case *">
        <input type="text" name="business_use_case" value={form.business_use_case}
          onChange={onChange} onFocus={focus} onBlur={blur}
          placeholder="e.g. Automate compliance reporting across 12 regions"
          required style={inputStyle} />
      </Field>

      {/* AE + SE */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label="Account Executive (AE)">
          <input type="text" name="ae_name" value={form.ae_name}
            onChange={onChange} onFocus={focus} onBlur={blur}
            placeholder="Leave blank to auto-generate" style={inputStyle} />
        </Field>
        <Field label="Sales Engineer (SE)">
          <input type="text" name="se_name" value={form.se_name}
            onChange={onChange} onFocus={focus} onBlur={blur}
            placeholder="Leave blank to auto-generate" style={inputStyle} />
        </Field>
      </div>

      {/* Company + Industry + Deal size */}
      <Field label="Company Name">
        <input type="text" name="company_name" value={form.company_name}
          onChange={onChange} onFocus={focus} onBlur={blur}
          placeholder="Leave blank to auto-generate" style={inputStyle} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label="Industry">
          <select name="industry" value={form.industry} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            {INDUSTRIES.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
        </Field>
        <Field label="Deal Size">
          <select name="deal_size" value={form.deal_size} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            {DEAL_SIZES.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>
      </div>

      {/* Outcome + Complexity + Objection + Urgency */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label="Deal Outcome">
          <select name="deal_outcome" value={form.deal_outcome} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="closed_won">Closed Won</option>
            <option value="closed_lost">Closed Lost</option>
          </select>
        </Field>
        <Field label="Complexity">
          <select name="complexity" value={form.complexity} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="simple">Simple</option>
            <option value="normal">Normal</option>
            <option value="messy">Messy</option>
          </select>
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label="Main Objection">
          <select name="main_objection" value={form.main_objection} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            {OBJECTIONS.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        </Field>
        <Field label="Buyer Urgency">
          <select name="buyer_urgency" value={form.buyer_urgency} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </Field>
      </div>

      {/* Sentiment */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <Field label="Starting Sentiment">
          <select name="starting_sentiment" value={form.starting_sentiment} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="concerned">Concerned</option>
            <option value="negative">Negative</option>
          </select>
        </Field>
        <Field label="Ending Sentiment">
          <select name="ending_sentiment" value={form.ending_sentiment} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="concerned">Concerned</option>
            <option value="negative">Negative</option>
          </select>
        </Field>
      </div>

      {/* Champion Entry */}
      <Field label="Champion Entry">
        <select name="champion_entry" value={form.champion_entry} onChange={onChange} onFocus={focus} onBlur={blur} style={inputStyle}>
          <option value="none">None</option>
          <option value="before_discovery">Before Discovery</option>
          <option value="during_discovery">During Discovery</option>
          <option value="after_demo">After Demo</option>
          <option value="during_procurement">During Procurement</option>
          <option value="late_stage_rescue">Late Stage Rescue</option>
        </select>
      </Field>

      {loading && generationProgress > 0 && (
        <GenerationProgress progress={generationProgress} step={generationStep} onCancel={cancelGeneration} />
      )}

      <button type="submit" disabled={loading} style={{
        width: '100%', padding: '11px',
        background: loading ? 'var(--surface-hi)' : 'var(--teal)',
        color: loading ? 'var(--text-muted)' : '#fff',
        borderRadius: '6px', border: 'none',
        fontFamily: 'inherit', fontSize: '14px', fontWeight: '500',
        cursor: loading ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
      }}>
        {loading
          ? generationProgress === 0
            ? <><div className="spinner" />Connecting...</>
            : 'Generating...'
          : 'Generate Series Deal'}
      </button>
    </form>
  )
}

export default SeriesPanel
