import React from 'react'
import { useNavigate } from 'react-router-dom'

const EmptyState = () => {
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div style={{ textAlign: 'center', maxWidth: '360px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: '600', color: 'var(--text)', marginBottom: '10px' }}>
          No deal selected
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px', lineHeight: '1.6' }}>
          Generate a synthetic B2B sales deal to analyze, or select one from the sidebar.
        </p>
        <button
          onClick={() => navigate('/new')}
          style={{
            padding: '9px 22px',
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
          Create New Deal
        </button>
      </div>
    </div>
  )
}

export default EmptyState
