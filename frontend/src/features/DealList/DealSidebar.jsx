import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDealContext } from '../../context/DealContext'
import Loading from '../../components/Loading'
import ErrorMessage from '../../components/ErrorMessage'

const DealSidebar = () => {
  const navigate = useNavigate()
  const { dealsList, listLoading, listError, setListError, deleteDeal } = useDealContext()
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  const handleNewDeal = () => navigate('/new')
  const handleSelectDeal = (dealId) => navigate(`/deals/${dealId}`)

  const handleDeleteClick = (e, dealId) => {
    e.stopPropagation()
    setConfirmDeleteId(dealId)
  }

  const handleConfirmDelete = (e, dealId) => {
    e.stopPropagation()
    setConfirmDeleteId(null)
    deleteDeal(dealId)
  }

  const handleCancelDelete = (e) => {
    e.stopPropagation()
    setConfirmDeleteId(null)
  }

  const formatDate = (dateStr) => new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid var(--rule)' }}>
        <button
          onClick={handleNewDeal}
          style={{
            width: '100%',
            padding: '8px 16px',
            background: 'var(--teal)',
            color: '#fff',
            borderRadius: '6px',
            border: 'none',
            fontFamily: 'inherit',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'opacity 0.15s',
          }}
          onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
          onMouseLeave={e => e.currentTarget.style.opacity = '1'}
        >
          + New Deal
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {listError && (
          <div style={{ padding: '16px' }}>
            <ErrorMessage message={listError} onRetry={() => setListError(null)} />
          </div>
        )}

        {listLoading ? (
          <div style={{ padding: '16px' }}><Loading label="Loading deals..." /></div>
        ) : dealsList.length === 0 ? (
          <div style={{ padding: '16px', textAlign: 'center', fontSize: '14px', color: 'var(--text-muted)' }}>
            No deals yet. Create one to get started.
          </div>
        ) : (
          <div style={{ padding: '8px' }}>
            {dealsList.map((deal) => {
              const isWon = deal.deal_outcome === 'closed_won'
              const isPendingDelete = confirmDeleteId === deal.deal_id
              return (
                <div
                  key={deal.deal_id}
                  onClick={() => handleSelectDeal(deal.deal_id)}
                  style={{
                    padding: '12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'background 0.15s',
                    marginBottom: '2px',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hi)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {deal.company_name}
                  </div>

                  <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '500',
                      background: isWon ? 'var(--teal-mid)' : 'rgba(239,68,68,0.12)',
                      color: isWon ? 'var(--teal)' : '#f87171',
                    }}>
                      {isWon ? 'Won' : 'Lost'}
                    </span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '500',
                      background: 'rgba(136,136,160,0.12)',
                      color: 'var(--text-muted)',
                    }}>
                      {deal.complexity.charAt(0).toUpperCase() + deal.complexity.slice(1)}
                    </span>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                    {formatDate(deal.generated_at)}
                  </div>

                  {isPendingDelete ? (
                    <div style={{ marginTop: '6px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Delete?</span>
                      <button
                        onClick={(e) => handleConfirmDelete(e, deal.deal_id)}
                        style={{ fontSize: '11px', color: '#f87171', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', padding: 0 }}
                      >
                        Yes
                      </button>
                      <button
                        onClick={handleCancelDelete}
                        style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', padding: 0 }}
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => handleDeleteClick(e, deal.deal_id)}
                      style={{ marginTop: '6px', fontSize: '11px', color: '#f87171', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', padding: 0 }}
                    >
                      Delete
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default DealSidebar
