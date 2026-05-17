import React from 'react'

const SentimentArc = ({ metadata, events }) => {
  const stages = metadata.sentiment_arc

  const sentimentColor = {
    positive: 'var(--teal)',
    neutral:  'var(--text-muted)',
    concerned:'var(--amber)',
    negative: '#f87171',
  }

  const sentimentBg = {
    positive: 'var(--teal-low)',
    neutral:  'rgba(136,136,160,0.06)',
    concerned:'rgba(232,164,74,0.07)',
    negative: 'rgba(239,68,68,0.07)',
  }

  const sentimentBorder = {
    positive: 'var(--teal-border)',
    neutral:  'rgba(136,136,160,0.18)',
    concerned:'rgba(232,164,74,0.22)',
    negative: 'rgba(239,68,68,0.22)',
  }

  // Derive a 1-sentence brief from the first event in each stage
  const getBrief = (stageName) => {
    const stageEvents = events
      .filter(e => e.stage === stageName)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

    if (!stageEvents.length) return null
    const e = stageEvents[0]
    if (e.record_type === 'call') {
      const s = e.summary || ''
      return s.split('.')[0] + '.'
    }
    if (e.record_type === 'email') return e.subject || null
    if (e.record_type === 'crm_note') return e.note_preview || null
    return null
  }

  return (
    <div>
      <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text)', marginBottom: '24px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Sentiment Arc
      </h2>

      <div style={{ display: 'flex', alignItems: 'stretch', gap: '0', overflowX: 'auto', paddingBottom: '4px' }}>
        {stages.map((stage, i) => {
          const color = sentimentColor[stage.sentiment] || 'var(--text-muted)'
          const brief = getBrief(stage.stage)

          return (
            <React.Fragment key={stage.stage}>
              {/* Card */}
              <div style={{
                flex: '1',
                minWidth: '140px',
                background: sentimentBg[stage.sentiment],
                border: `1px solid ${sentimentBorder[stage.sentiment]}`,
                borderRadius: '8px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                minHeight: '130px',
              }}>
                {/* Stage name pinned to top */}
                <div style={{ fontSize: '11px', fontWeight: '600', color: color, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
                  {stage.stage}
                </div>

                {/* Sentiment + brief centered in remaining space */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '6px' }}>
                  <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)' }}>
                    {stage.sentiment.charAt(0).toUpperCase() + stage.sentiment.slice(1)}
                  </div>
                  {brief && (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                      {brief}
                    </div>
                  )}
                </div>
              </div>

              {/* Arrow between cards */}
              {i < stages.length - 1 && (
                <div style={{ display: 'flex', alignItems: 'center', padding: '0 8px', color: 'var(--text-dim)', fontSize: '14px', flexShrink: 0 }}>
                  →
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

export default SentimentArc
