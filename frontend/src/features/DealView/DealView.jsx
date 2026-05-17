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

  return (
    <div style={{ ...pad, display: 'flex', flexDirection: 'column', gap: '40px' }}>
      <DealHeader deal={currentDeal} />
      <StakeholderGrid metadata={currentDeal.metadata} />
      <SentimentArc metadata={currentDeal.metadata} events={currentDeal.events || []} />
      <DealTimeline deal={currentDeal} />
    </div>
  )
}

export default DealView
