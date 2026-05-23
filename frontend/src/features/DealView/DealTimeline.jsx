import React, { useState, useMemo } from 'react'
import TimelineEvent from '../../components/TimelineEvent'
import SlackView from './SlackView'

const STAGE_NAMES = ['Prospecting', 'Discovery', 'Demo', 'Evaluation', 'Negotiation', 'Closed']

const CHAMPION_ENTRY_TO_STAGE = {
  before_discovery: 'Prospecting',
  during_discovery: 'Discovery',
  after_demo: 'Demo',
  during_procurement: 'Evaluation',
  late_stage_rescue: 'Negotiation',
}

const TabBar = ({ activeTab, setActiveTab, hasCS, hasSlack }) => {
  if (!hasCS && !hasSlack) return null
  const tab = (id, label) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        padding: '6px 16px',
        fontSize: '12px',
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: '0.07em',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        transition: 'background 0.15s, color 0.15s',
        background: activeTab === id ? 'var(--accent, #a78bfa)' : 'transparent',
        color: activeTab === id ? '#fff' : 'var(--text-muted)',
      }}
    >
      {label}
    </button>
  )
  return (
    <div style={{
      display: 'inline-flex',
      gap: '4px',
      background: 'var(--surface-raised, rgba(255,255,255,0.05))',
      borderRadius: '6px',
      padding: '4px',
      marginBottom: '28px',
      border: '1px solid var(--rule)',
    }}>
      {tab('sales', 'Sales Timeline')}
      {tab('cs', 'CS Timeline')}
      {tab('slack', 'Slack')}
    </div>
  )
}

const SalesTimeline = ({ events, metadata }) => {
  const [collapsedStages, setCollapsedStages] = useState({})
  const toggleStage = (stageName) =>
    setCollapsedStages(prev => ({ ...prev, [stageName]: !prev[stageName] }))

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
  )
}

const CSTimeline = ({ events, metadata }) => {
  const sorted = useMemo(
    () => [...events].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)),
    [events]
  )

  if (sorted.length === 0) {
    return (
      <p style={{ fontSize: '13px', color: 'var(--text-dim)', fontStyle: 'italic' }}>
        No CS events found for this deal.
      </p>
    )
  }

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '24px',
      }}>
        <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
        <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Post-Close · {sorted.length} event{sorted.length !== 1 ? 's' : ''}
        </span>
        <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sorted.map(event => (
          <TimelineEvent key={event.id} event={event} allEvents={events} stakeholders={metadata.stakeholders} />
        ))}
      </div>
    </div>
  )
}

const DealTimeline = ({ deal }) => {
  const events = deal.events || []
  const metadata = deal.metadata
  const [activeTab, setActiveTab] = useState('sales')

  const { salesEvents, csEvents, slackEvents } = useMemo(() => ({
    salesEvents: events.filter(e => !e.record_type?.startsWith('support')),
    csEvents: events.filter(e => e.record_type?.startsWith('support')),
    slackEvents: (deal.timeline_events || []).filter(e => e.record_type?.startsWith('slack')),
  }), [events, deal.timeline_events])

  const hasCS = csEvents.length > 0
  const hasSlack = slackEvents.length > 0

  return (
    <div>
      <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text)', marginBottom: '20px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Timeline
      </h2>

      <TabBar activeTab={activeTab} setActiveTab={setActiveTab} hasCS={hasCS} hasSlack={hasSlack} />

      {activeTab === 'sales' && <SalesTimeline events={salesEvents} metadata={metadata} />}
      {activeTab === 'cs' && <CSTimeline events={csEvents} metadata={metadata} />}
      {activeTab === 'slack' && <div style={{ marginTop: '24px' }}><SlackView deal={deal} /></div>}
    </div>
  )
}

export default DealTimeline
