import React from 'react'

const supportColors = {
  champion:  { bg: 'rgba(61,168,148,0.10)',  border: 'rgba(61,168,148,0.28)',  text: 'var(--teal)' },
  supporter: { bg: 'rgba(61,168,148,0.06)',  border: 'rgba(61,168,148,0.16)',  text: 'var(--teal)' },
  neutral:   { bg: 'rgba(136,136,160,0.08)', border: 'rgba(136,136,160,0.18)', text: 'var(--text-muted)' },
  skeptic:   { bg: 'rgba(232,164,74,0.08)',  border: 'rgba(232,164,74,0.22)',  text: 'var(--amber)' },
  blocker:   { bg: 'rgba(239,68,68,0.08)',   border: 'rgba(239,68,68,0.22)',   text: '#f87171' },
}

const influenceDots = { high: 3, medium: 2, low: 1 }

const StakeholderGrid = ({ metadata }) => {
  const stakeholders = metadata.stakeholders
  if (!stakeholders?.length) return null

  return (
    <div>
      <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text)', marginBottom: '24px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Stakeholders
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px' }}>
        {stakeholders.map((s) => {
          const palette = supportColors[s.support_level] || supportColors.neutral
          const dots = influenceDots[s.influence_level] || 1

          return (
            <div
              key={s.id}
              style={{
                background: palette.bg,
                border: `1px solid ${palette.border}`,
                borderRadius: '8px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              {/* Name + champion badge */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text)' }}>{s.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{s.title}</div>
                </div>
                {s.is_champion && (
                  <span style={{
                    fontSize: '10px', fontWeight: '600', padding: '2px 7px',
                    background: 'var(--teal-mid)', color: 'var(--teal)',
                    borderRadius: '4px', whiteSpace: 'nowrap', flexShrink: 0,
                    textTransform: 'uppercase', letterSpacing: '0.06em',
                  }}>
                    Champion
                  </span>
                )}
              </div>

              {/* Archetype */}
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                {s.archetype}
              </div>

              {/* Email */}
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', wordBreak: 'break-all' }}>
                {s.email}
              </div>

              {/* Support level + influence */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
                <span style={{
                  fontSize: '11px', fontWeight: '600', padding: '2px 8px',
                  background: palette.bg, color: palette.text,
                  border: `1px solid ${palette.border}`, borderRadius: '4px',
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                  {s.support_level}
                </span>

                {/* Influence dots */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-dim)', marginRight: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Influence</span>
                  {[1, 2, 3].map(i => (
                    <div key={i} style={{
                      width: '7px', height: '7px', borderRadius: '50%',
                      background: i <= dots ? palette.text : 'var(--rule)',
                    }} />
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default StakeholderGrid
