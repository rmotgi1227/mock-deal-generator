import React, { useState, useMemo } from 'react'
import TimelineEvent from '../../components/TimelineEvent'

const STAGE_NAMES = ['Prospecting', 'Discovery', 'Demo', 'Evaluation', 'Negotiation', 'Closed']

// Maps champion_entry config value to the stage where the champion enters
const CHAMPION_ENTRY_TO_STAGE = {
  before_discovery: 'Prospecting',
  during_discovery: 'Discovery',
  after_demo: 'Demo',
  during_procurement: 'Evaluation',
  late_stage_rescue: 'Negotiation',
}

const DealTimeline = ({ deal }) => {
  const events = deal.events || []
  const metadata = deal.metadata
  const [collapsedStages, setCollapsedStages] = useState({})

  const toggleStage = (stageName) => {
    setCollapsedStages(prev => ({ ...prev, [stageName]: !prev[stageName] }))
  }

  const eventsByStage = useMemo(() => {
    const grouped = { Prospecting: [], Discovery: [], Demo: [], Evaluation: [], Negotiation: [], Closed: [] }
    events.forEach(event => { if (grouped[event.stage]) grouped[event.stage].push(event) })
    Object.keys(grouped).forEach(stage => {
      grouped[stage].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    })
    return grouped
  }, [events])

  const championEntryStage = CHAMPION_ENTRY_TO_STAGE[metadata.config.champion_entry] || null

  return (
    <div>
      <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text)', marginBottom: '28px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Timeline
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {STAGE_NAMES.map(stageName => {
          const stageEvents = eventsByStage[stageName] || []
          const championEntered = championEntryStage === stageName
          const isCollapsed = collapsedStages[stageName]

          return (
            <div key={stageName}>
              <button
                onClick={() => toggleStage(stageName)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  width: '100%',
                  marginBottom: '16px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  gap: '12px',
                }}
              >
                <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {stageName}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>{isCollapsed ? '▶' : '▼'}</span>
                </div>
                <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
              </button>

              {!isCollapsed && (
                <div>
                  {championEntered && (
                    <div style={{
                      background: 'var(--teal-low)',
                      border: '1px solid var(--teal-border)',
                      borderRadius: '6px',
                      padding: '10px 14px',
                      marginBottom: '12px',
                      fontSize: '12px',
                      color: 'var(--teal)',
                    }}>
                      Champion entered in this stage
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {stageEvents.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--text-dim)', fontStyle: 'italic' }}>No events in this stage</p>
                    ) : (
                      stageEvents.map(event => (
                        <TimelineEvent key={event.id} event={event} allEvents={events} stakeholders={metadata.stakeholders} />
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default DealTimeline
