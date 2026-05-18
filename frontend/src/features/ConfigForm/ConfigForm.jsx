import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDealContext } from '../../context/DealContext'
import ErrorMessage from '../../components/ErrorMessage'
import GenerationProgress from '../../components/GenerationProgress'
import BulkGeneratePanel from './BulkGeneratePanel'

const inputStyle = {
  width: '100%',
  padding: '9px 12px',
  background: 'var(--surface)',
  border: '1px solid var(--rule)',
  borderRadius: '6px',
  color: 'var(--text)',
  fontFamily: 'inherit',
  fontSize: '14px',
  outline: 'none',
  transition: 'border-color 0.15s',
}

const labelStyle = {
  display: 'block',
  fontSize: '12px',
  fontWeight: '500',
  color: 'var(--text-muted)',
  marginBottom: '6px',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
}

const Field = ({ label, children }) => (
  <div>
    <label style={labelStyle}>{label}</label>
    {children}
  </div>
)

const ConfigForm = () => {
  const navigate = useNavigate()
  const { generateDealStream, cancelGeneration, loading, error, setError, generationProgress, generationStep } = useDealContext()
  const [mode, setMode] = useState('single') // 'single' | 'bulk'

  const [formData, setFormData] = useState({
    company_name: '',
    industry: 'Fintech',
    deal_size: '$75k ARR',
    sales_cycle_length_days: 45,
    starting_sentiment: 'neutral',
    ending_sentiment: 'positive',
    deal_outcome: 'closed_won',
    champion_entry: 'after_demo',
    main_objection: 'Security Review',
    buyer_urgency: 'medium',
    num_calls: 5,
    emails_per_stage: 2,
    num_stakeholders: 3,
    complexity: 'messy',
  })

  const [csEnabled, setCsEnabled] = useState(false)
  const [csData, setCsData] = useState({
    adoption_challenge: 'integration_complexity',
    support_contact_frequency: 'medium',
    churn_probability: 0.5,
    post_close_days: 30,
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? null : (
        ['sales_cycle_length_days', 'num_calls', 'emails_per_stage', 'num_stakeholders'].includes(name)
          ? parseInt(value)
          : value
      ),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const payload = {
        ...formData,
        company_name: formData.company_name === '' ? null : formData.company_name,
        cs_scenario: csEnabled ? { enabled: true, ...csData } : null,
      }
      const result = await generateDealStream(payload)
      navigate(`/deals/${result.deal_id}`)
    } catch (err) {
      // Error already set in context via generateDealStream; navigate is not called on failure
    }
  }

  const focusStyle = (e) => e.target.style.borderColor = 'var(--teal-border)'
  const blurStyle = (e) => e.target.style.borderColor = 'var(--rule)'

  const tabStyle = (active) => ({
    padding: '7px 18px',
    background: active ? 'var(--teal)' : 'var(--surface)',
    color: active ? '#fff' : 'var(--text-muted)',
    border: '1px solid',
    borderColor: active ? 'var(--teal)' : 'var(--rule)',
    borderRadius: '6px',
    fontFamily: 'inherit',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
  })

  return (
    <div style={{ minHeight: '100%', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '60px 48px' }}>
      <div style={{ width: '100%', maxWidth: '760px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text)', marginBottom: '6px', letterSpacing: '-0.5px' }}>
          Generate Deal
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Configure parameters for a synthetic B2B sales deal.
        </p>

        {/* Mode tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '32px' }}>
          <button style={tabStyle(mode === 'single')} onClick={() => setMode('single')}>Single Deal</button>
          <button style={tabStyle(mode === 'bulk')} onClick={() => setMode('bulk')}>Bulk Random</button>
        </div>

        {mode === 'bulk' && <BulkGeneratePanel />}

        {mode === 'single' && <>
        {error && <div style={{ marginBottom: '24px' }}><ErrorMessage message={error} /></div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Row 1: Company Name full width */}
          <Field label="Company Name">
            <input
              type="text"
              name="company_name"
              value={formData.company_name}
              onChange={handleChange}
              onFocus={focusStyle}
              onBlur={blurStyle}
              placeholder="Leave blank to auto-generate"
              style={inputStyle}
            />
          </Field>

          {/* Row 2: Industry + Deal Size */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Field label="Industry">
              <input type="text" name="industry" value={formData.industry} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle} />
            </Field>
            <Field label="Deal Size">
              <input type="text" name="deal_size" value={formData.deal_size} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle} />
            </Field>
          </div>

          {/* Row 3: Starting Sentiment + Ending Sentiment */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Field label="Starting Sentiment">
              <select name="starting_sentiment" value={formData.starting_sentiment} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="concerned">Concerned</option>
                <option value="negative">Negative</option>
              </select>
            </Field>
            <Field label="Ending Sentiment">
              <select name="ending_sentiment" value={formData.ending_sentiment} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="concerned">Concerned</option>
                <option value="negative">Negative</option>
              </select>
            </Field>
          </div>

          {/* Row 4: Deal Outcome + Champion Entry */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Field label="Deal Outcome">
              <select name="deal_outcome" value={formData.deal_outcome} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                <option value="closed_won">Closed Won</option>
                <option value="closed_lost">Closed Lost</option>
              </select>
            </Field>
            <Field label="Champion Entry">
              <select name="champion_entry" value={formData.champion_entry} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                <option value="none">None</option>
                <option value="before_discovery">Before Discovery</option>
                <option value="during_discovery">During Discovery</option>
                <option value="after_demo">After Demo</option>
                <option value="during_procurement">During Procurement</option>
                <option value="late_stage_rescue">Late Stage Rescue</option>
              </select>
            </Field>
          </div>

          {/* Row 5: Main Objection + Buyer Urgency */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Field label="Main Objection">
              <input type="text" name="main_objection" value={formData.main_objection} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle} />
            </Field>
            <Field label="Buyer Urgency">
              <select name="buyer_urgency" value={formData.buyer_urgency} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </Field>
          </div>

          {/* Row 6: Sales Cycle + Num Calls + Emails Per Stage + Stakeholders */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '20px' }}>
            <Field label="Sales Cycle (days)">
              <input type="number" name="sales_cycle_length_days" value={formData.sales_cycle_length_days} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} min="14" max="180" style={inputStyle} />
            </Field>
            <Field label="Number of Calls">
              <input type="number" name="num_calls" value={formData.num_calls} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} min="1" max="10" style={inputStyle} />
            </Field>
            <Field label="Emails Per Stage">
              <input type="number" name="emails_per_stage" value={formData.emails_per_stage} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} min="1" max="5" style={inputStyle} />
            </Field>
            <Field label="Stakeholders">
              <input type="number" name="num_stakeholders" value={formData.num_stakeholders} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} min="2" max="8" style={inputStyle} />
            </Field>
          </div>

          {/* Row 7: Complexity full width */}
          <Field label="Complexity">
            <select name="complexity" value={formData.complexity} onChange={handleChange} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
              <option value="simple">Simple</option>
              <option value="normal">Normal</option>
              <option value="messy">Messy</option>
            </select>
          </Field>

          {/* CS Scenario Section */}
          <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: csEnabled ? '20px' : '0' }}>
              <label style={{ ...labelStyle, marginBottom: 0 }}>Customer Success Scenario</label>
              <button
                type="button"
                onClick={() => setCsEnabled(p => !p)}
                style={{
                  padding: '4px 12px',
                  background: csEnabled ? 'var(--teal)' : 'var(--surface)',
                  color: csEnabled ? '#fff' : 'var(--text-muted)',
                  border: '1px solid',
                  borderColor: csEnabled ? 'var(--teal)' : 'var(--rule)',
                  borderRadius: '20px',
                  fontFamily: 'inherit',
                  fontSize: '12px',
                  fontWeight: '500',
                  cursor: 'pointer',
                }}
              >
                {csEnabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>

            {csEnabled && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <Field label="Adoption Challenge">
                    <select value={csData.adoption_challenge} onChange={e => setCsData(p => ({ ...p, adoption_challenge: e.target.value }))} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                      <option value="integration_complexity">Integration Complexity</option>
                      <option value="training_gap">Training Gap</option>
                      <option value="workflow_mismatch">Workflow Mismatch</option>
                      <option value="performance_issues">Performance Issues</option>
                      <option value="unclear_roi">Unclear ROI</option>
                    </select>
                  </Field>
                  <Field label="Support Frequency">
                    <select value={csData.support_contact_frequency} onChange={e => setCsData(p => ({ ...p, support_contact_frequency: e.target.value }))} onFocus={focusStyle} onBlur={blurStyle} style={inputStyle}>
                      <option value="low">Low (2-3 interactions)</option>
                      <option value="medium">Medium (5-7 interactions)</option>
                      <option value="high">High (8-12 interactions)</option>
                    </select>
                  </Field>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  <Field label={`Churn Probability (${Math.round(csData.churn_probability * 100)}%)`}>
                    <input
                      type="range"
                      min="0" max="1" step="0.05"
                      value={csData.churn_probability}
                      onChange={e => setCsData(p => ({ ...p, churn_probability: parseFloat(e.target.value) }))}
                      style={{ width: '100%', marginTop: '6px', accentColor: 'var(--teal)' }}
                    />
                  </Field>
                  <Field label="Post-Close Days">
                    <input
                      type="number"
                      min="7" max="180"
                      value={csData.post_close_days}
                      onChange={e => setCsData(p => ({ ...p, post_close_days: parseInt(e.target.value) }))}
                      onFocus={focusStyle}
                      onBlur={blurStyle}
                      style={inputStyle}
                    />
                  </Field>
                </div>
              </div>
            )}
          </div>

          {loading && generationProgress > 0 && (
            <GenerationProgress progress={generationProgress} step={generationStep} onCancel={cancelGeneration} />
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '11px',
              background: loading ? 'var(--surface-hi)' : 'var(--teal)',
              color: loading ? 'var(--text-muted)' : '#fff',
              borderRadius: '6px',
              border: 'none',
              fontFamily: 'inherit',
              fontSize: '14px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'opacity 0.15s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {loading ? (
              generationProgress === 0 ? (
                <><div className="spinner" />Connecting...</>
              ) : 'Generating...'
            ) : 'Generate Deal'}
          </button>
        </form>
        </>}
      </div>
    </div>
  )
}

export default ConfigForm
