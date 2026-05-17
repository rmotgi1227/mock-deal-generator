import React from 'react'

const ErrorMessage = ({ message, onRetry }) => {
  if (!message) return null
  return (
    <div style={{
      background: 'rgba(239,68,68,0.08)',
      border: '1px solid rgba(239,68,68,0.25)',
      borderRadius: '6px',
      padding: '12px 16px',
      marginBottom: '16px',
    }}>
      <p style={{ fontSize: '13px', color: '#f87171' }}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: '8px',
            padding: '4px 12px',
            background: 'rgba(239,68,68,0.12)',
            color: '#f87171',
            borderRadius: '4px',
            border: 'none',
            fontSize: '12px',
            fontFamily: 'inherit',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      )}
    </div>
  )
}

export default ErrorMessage
