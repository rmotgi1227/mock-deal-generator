import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDealContext } from '../../context/DealContext'
import DealHeader from './DealHeader'
import SentimentArc from './SentimentArc'
import DealTimeline from './DealTimeline'
import Loading from '../../components/Loading'
import ErrorMessage from '../../components/ErrorMessage'

// Main deal detail page
const DealView = () => {
  const { deal_id } = useParams()
  const { currentDeal, loading, error, loadDeal, setError } = useDealContext()

  // Load deal on mount or when deal_id changes
  useEffect(() => {
    if (deal_id) {
      loadDeal(deal_id).catch(() => {
        // Error already set in context
      })
    }
  }, [deal_id, loadDeal])

  if (loading) {
    return (
      <div className="p-8">
        <Loading label="Loading deal..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <ErrorMessage message={error} onRetry={() => setError(null)} />
      </div>
    )
  }

  if (!currentDeal) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No deal found</p>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      <DealHeader deal={currentDeal} />
      <SentimentArc metadata={currentDeal.metadata} />
      <DealTimeline deal={currentDeal} />
    </div>
  )
}

export default DealView
