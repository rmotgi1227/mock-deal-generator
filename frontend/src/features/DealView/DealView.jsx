import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDealContext } from '../../context/DealContext'
import DealHeader from './DealHeader'
import StakeholderGrid from './StakeholderGrid'
import SentimentArc from './SentimentArc'
import DealTimeline from './DealTimeline'
import Loading from '../../components/Loading'
import ErrorMessage from '../../components/ErrorMessage'

// Main deal detail page
const DealView = () => {
  const { deal_id } = useParams()
  const { currentDeal, detailLoading, detailError, loadDeal, setDetailError } = useDealContext()

  // Load deal on mount or when deal_id changes
  useEffect(() => {
    if (deal_id) {
      loadDeal(deal_id).catch(() => {
        // Error already set in context
      })
    }
  }, [deal_id, loadDeal])

  const pad = { padding: '40px 48px' }

  if (detailLoading) return <div style={pad}><Loading label="Loading deal..." /></div>

  if (detailError) return <div style={pad}><ErrorMessage message={detailError} onRetry={() => setDetailError(null)} /></div>

  if (!currentDeal) return (
    <div style={{ ...pad, color: 'var(--text-muted)', fontSize: '14px' }}>No deal found</div>
  )

  const renderCSContext = () => {
    const csScenario = currentDeal.metadata.cs_scenario
    if (!csScenario || !csScenario.enabled) return null

    const fmt = (val) => {
      if (val === null || val === undefined) return val
      return String(val).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    }

    return (
      <div style={{
        background: 'rgba(232,164,74,0.08)',
        border: '1px solid rgba(232,164,74,0.3)',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px',
      }}>
        <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--amber)' }}>⚠</span>
          Customer Success Risk
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px',
        }}>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Adoption Challenge</div>
            <div style={{ fontSize: '13px', color: 'var(--text)' }}>{fmt(csScenario.adoption_challenge)}</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Support Frequency</div>
            <div style={{ fontSize: '13px', color: 'var(--text)' }}>{fmt(csScenario.support_contact_frequency)}</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Churn Probability</div>
            <div style={{ fontSize: '13px', color: 'var(--text)' }}>{(csScenario.churn_probability * 100).toFixed(0)}%</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-dim)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Support Events</div>
            <div style={{ fontSize: '13px', color: 'var(--text)' }}>{currentDeal.metadata.support_events_count || 0}</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ ...pad, display: 'flex', flexDirection: 'column', gap: '40px' }}>
      <DealHeader deal={currentDeal} />
      {renderCSContext()}
      <StakeholderGrid metadata={currentDeal.metadata} />
      <SentimentArc metadata={currentDeal.metadata} events={currentDeal.events || []} />
      <DealTimeline deal={currentDeal} />
    </div>
  )
}

export default DealView
