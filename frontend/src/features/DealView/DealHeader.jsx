import React, { useState } from 'react'

const DealHeader = ({ deal }) => {
  const [showConfig, setShowConfig] = useState(false)
  const metadata = deal.metadata

  const fmt = (val) => {
    if (val === null || val === undefined) return val
    return String(val).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  }

  const startDate = new Date(metadata.deal_start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const endDate = new Date(metadata.deal_end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const durationDays = Math.round(
    (new Date(metadata.deal_end_date) - new Date(metadata.deal_start_date)) / (1000 * 60 * 60 * 24)
  )

  const isWon = metadata.deal_outcome === 'closed_won'

  const Badge = ({ children, color = 'muted' }) => {
    const styles = {
      teal: { background: 'var(--teal-mid)', color: 'var(--teal)' },
      red: { background: 'rgba(239,68,68,0.12)', color: '#f87171' },
      amber: { background: 'rgba(232,164,74,0.12)', color: 'var(--amber)' },
      muted: { background: 'rgba(136,136,160,0.12)', color: 'var(--text-muted)' },
    }
    return (
      <span style={{
        padding: '3px 10px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: '500',
        ...styles[color],
      }}>
        {children}
      </span>
    )
  }

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', color: 'var(--text)', marginBottom: '14px', letterSpacing: '-0.5px' }}>
        {metadata.company.name}
      </h1>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
        <Badge color="teal">{metadata.config.deal_size}</Badge>
        <Badge color="muted">{metadata.config.industry}</Badge>
        <Badge color={isWon ? 'teal' : 'red'}>{isWon ? 'Closed Won' : 'Closed Lost'}</Badge>
        <Badge color="amber">{fmt(metadata.config.complexity)}</Badge>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        {startDate} – {endDate} · {durationDays} days
      </p>

      <button
        onClick={() => setShowConfig(!showConfig)}
        style={{
          fontSize: '13px',
          color: 'var(--teal)',
          background: 'none',
          border: 'none',
          fontFamily: 'inherit',
          cursor: 'pointer',
          marginBottom: '16px',
          padding: 0,
        }}
      >
        {showConfig ? '▼' : '▶'} Configuration
      </button>

      {showConfig && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--rule)',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px',
        }}>
          {[
            ['Industry', metadata.config.industry],
            ['Deal Size', metadata.config.deal_size],
            ['Sales Cycle', `${metadata.config.sales_cycle_length_days} days`],
            ['Starting Sentiment', fmt(metadata.config.starting_sentiment)],
            ['Ending Sentiment', fmt(metadata.config.ending_sentiment)],
            ['Outcome', fmt(metadata.deal_outcome)],
            ['Champion Entry', fmt(metadata.config.champion_entry)],
            ['Main Objection', metadata.config.main_objection],
            ['Buyer Urgency', fmt(metadata.config.buyer_urgency)],
            ['Calls', metadata.config.num_calls],
            ['Emails / Stage', metadata.config.emails_per_stage],
            ['Stakeholders', metadata.config.num_stakeholders],
            ['Complexity', fmt(metadata.config.complexity)],
            ['Sales Rep', `${metadata.sales_rep.name} (${metadata.sales_rep.title})`],
          ].map(([label, value]) => (
            <div key={label}>
              <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
              <div style={{ fontSize: '13px', color: 'var(--text)' }}>{value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default DealHeader
