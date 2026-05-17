import React, { useState } from 'react'

const TimelineEvent = ({ event, allEvents, stakeholders }) => {
  const [expanded, setExpanded] = useState(false)

  const getStakeholderNames = (ids) =>
    ids.map(id => stakeholders.find(s => s.id === id)?.name || 'Unknown').join(', ')

  const formatDate = (timestamp) =>
    new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  const sentimentStyle = {
    positive: { background: 'var(--teal-mid)', color: 'var(--teal)' },
    neutral:  { background: 'rgba(136,136,160,0.12)', color: 'var(--text-muted)' },
    concerned:{ background: 'rgba(232,164,74,0.12)', color: 'var(--amber)' },
    negative: { background: 'rgba(239,68,68,0.12)', color: '#f87171' },
  }

  const CANONICAL = ['positive', 'neutral', 'concerned', 'negative']
  const normalizeSentiment = (s) => {
    if (!s) return 'neutral'
    const lower = s.toLowerCase()
    return CANONICAL.find(c => lower === c) || CANONICAL.find(c => lower.includes(c)) || 'neutral'
  }
  const sentimentKey = normalizeSentiment(event.sentiment)
  const sentimentLabel = sentimentKey.charAt(0).toUpperCase() + sentimentKey.slice(1)

  const typeLabel = { call: 'Call', email: 'Email', crm_note: 'Note' }[event.record_type] || '–'

  const cardStyle = {
    background: 'var(--surface)',
    border: '1px solid var(--rule)',
    borderRadius: '8px',
    padding: '14px 16px',
    cursor: 'pointer',
    transition: 'border-color 0.15s',
  }

  if (!expanded) {
    return (
      <div
        onClick={() => setExpanded(true)}
        style={cardStyle}
        onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--teal-border)'}
        onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--rule)'}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', paddingTop: '2px', minWidth: '36px' }}>
            {typeLabel}
          </span>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {event.record_type === 'call' ? event.title : event.record_type === 'email' ? event.subject : 'CRM Note'}
              </span>
              {event.record_type === 'email' && event.sender?.name && (
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{event.sender.name}</span>
              )}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
              {event.record_type === 'crm_note'
                ? event.author
                : event.record_type === 'call'
                ? getStakeholderNames(event.participants?.map(p => p.stakeholder_id) || [])
                : null}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
              {formatDate(event.timestamp)}
            </div>
          </div>

          <span style={{ fontSize: '11px', fontWeight: '500', padding: '3px 8px', borderRadius: '4px', whiteSpace: 'nowrap', flexShrink: 0, ...sentimentStyle[sentimentKey] }}>
            {sentimentLabel}
          </span>
        </div>
      </div>
    )
  }

  // Expanded
  return (
    <div
      onClick={() => setExpanded(false)}
      style={{ ...cardStyle, borderColor: 'var(--teal-border)', background: 'var(--surface-hi)' }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '16px', paddingBottom: '14px', borderBottom: '1px solid var(--rule)' }}>
        <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', paddingTop: '2px', minWidth: '36px' }}>
          {typeLabel}
        </span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text)', marginBottom: '4px' }}>
            {event.record_type === 'call' ? event.title : event.record_type === 'email' ? event.subject : 'CRM Note'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {event.record_type === 'crm_note' ? event.author
              : event.record_type === 'call' ? getStakeholderNames(event.participants?.map(p => p.stakeholder_id) || [])
              : null}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>{formatDate(event.timestamp)}</div>
        </div>
        <span style={{ fontSize: '11px', fontWeight: '500', padding: '3px 8px', borderRadius: '4px', flexShrink: 0, ...sentimentStyle[sentimentKey] }}>
          {sentimentLabel}
        </span>
      </div>

      {/* Call content */}
      {event.record_type === 'call' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Transcript</div>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--rule)', borderRadius: '6px', padding: '12px', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace', whiteSpace: 'pre-wrap', maxHeight: '320px', overflowY: 'auto', lineHeight: '1.6' }}>
              {event.transcript}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Summary</div>
            <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: '1.6' }}>{event.summary}</p>
          </div>
          {event.next_steps?.length > 0 && (
            <div>
              <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Next Steps</div>
              <ul style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {event.next_steps.map((step, i) => <li key={i} style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{step}</li>)}
              </ul>
            </div>
          )}
          {event.objections_raised?.length > 0 && (
            <div>
              <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Objections</div>
              <ul style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {event.objections_raised.map((obj, i) => <li key={i} style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{obj}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Email content */}
      {event.record_type === 'email' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--rule)', borderRadius: '6px', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text)' }}>{event.sender.name}</span>
            <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{formatDate(event.timestamp)}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            To: {event.recipients.map(r => r.name).join(', ')}
            {event.cc?.length > 0 && ` · CC: ${event.cc.map(c => c.name).join(', ')}`}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text)', lineHeight: '1.6' }}>{event.body}</div>
        </div>
      )}

      {/* CRM Note content */}
      {event.record_type === 'crm_note' && (
        <div>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>Internal Note</div>
          <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: '1.6', marginBottom: '10px' }}>{event.content}</p>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{event.author} · {formatDate(event.timestamp)}</div>
        </div>
      )}
    </div>
  )
}

export default TimelineEvent
