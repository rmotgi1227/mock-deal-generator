import React from 'react'

const Loading = ({ label = 'Loading...' }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px', gap: '10px' }}>
    <div className="spinner" />
    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{label}</span>
  </div>
)

export default Loading
