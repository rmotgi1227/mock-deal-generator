import React, { useState } from 'react'
import { useDealContext } from '../../context/DealContext'

const BulkGeneratePanel = () => {
  const { bulkGenerateStream, bulkLoading, bulkProgress, cancelGeneration } = useDealContext()
  const [count, setCount] = useState(5)
  const [done, setDone] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setDone(false)
    setError(null)
    try {
      await bulkGenerateStream(count)
      setDone(true)
    } catch (err) {
      setError(err.message || 'Bulk generation failed')
    }
  }

  const progressPct = bulkProgress.total > 0
    ? Math.round(((bulkProgress.completed + bulkProgress.failed) / bulkProgress.total) * 100)
    : 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '500', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Number of Deals
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <input
            type="range"
            min={1}
            max={20}
            value={count}
            onChange={e => setCount(Number(e.target.value))}
            disabled={bulkLoading}
            style={{ flex: 1, accentColor: 'var(--teal)' }}
          />
          <span style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text)', minWidth: '40px', textAlign: 'right' }}>
            {count}
          </span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
          All variables randomized — industry, deal size, complexity, sentiment, objections, and more.
          Runs {Math.min(count, 2)} deals concurrently with a shared rate limiter.
        </p>
      </div>

      {bulkLoading && bulkProgress.total > 0 && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              {bulkProgress.completed + bulkProgress.failed} of {bulkProgress.total} complete
              {bulkProgress.failed > 0 && <span style={{ color: '#e05c5c', marginLeft: '8px' }}>{bulkProgress.failed} failed</span>}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{progressPct}%</span>
          </div>
          <div style={{ height: '6px', background: 'var(--surface-hi)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progressPct}%`, background: 'var(--teal)', borderRadius: '3px', transition: 'width 0.4s ease' }} />
          </div>
        </div>
      )}

      {done && !bulkLoading && (
        <div style={{ padding: '12px 16px', background: 'var(--surface)', border: '1px solid var(--rule)', borderRadius: '6px', fontSize: '13px', color: 'var(--text)' }}>
          Done — {bulkProgress.completed} deal{bulkProgress.completed !== 1 ? 's' : ''} generated
          {bulkProgress.failed > 0 && <span style={{ color: '#e05c5c' }}>, {bulkProgress.failed} failed</span>}.
          Check the sidebar.
        </div>
      )}

      {error && (
        <div style={{ padding: '12px 16px', background: 'var(--surface)', border: '1px solid #e05c5c', borderRadius: '6px', fontSize: '13px', color: '#e05c5c' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleGenerate}
          disabled={bulkLoading}
          style={{
            flex: 1,
            padding: '11px',
            background: bulkLoading ? 'var(--surface-hi)' : 'var(--teal)',
            color: bulkLoading ? 'var(--text-muted)' : '#fff',
            borderRadius: '6px',
            border: 'none',
            fontFamily: 'inherit',
            fontSize: '14px',
            fontWeight: '500',
            cursor: bulkLoading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {bulkLoading ? (
            <><div className="spinner" />Generating {bulkProgress.completed + bulkProgress.failed}/{bulkProgress.total}...</>
          ) : `Generate ${count} Random Deal${count !== 1 ? 's' : ''}`}
        </button>

        {bulkLoading && (
          <button
            onClick={cancelGeneration}
            style={{
              padding: '11px 16px',
              background: 'var(--surface)',
              color: 'var(--text-muted)',
              borderRadius: '6px',
              border: '1px solid var(--rule)',
              fontFamily: 'inherit',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

export default BulkGeneratePanel
