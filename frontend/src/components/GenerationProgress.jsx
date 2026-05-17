import React from 'react'

const GenerationProgress = ({ progress, step, onCancel }) => (
  <div style={{ width: '100%' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{step}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '13px', color: 'var(--teal)', fontWeight: '500' }}>{Math.round(progress)}%</span>
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              fontSize: '12px',
              color: '#f87171',
              background: 'none',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '4px',
              padding: '2px 8px',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Stop
          </button>
        )}
      </div>
    </div>
    <div style={{ width: '100%', height: '3px', background: 'var(--surface-hi)', borderRadius: '2px', overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          width: `${progress}%`,
          background: 'var(--teal)',
          borderRadius: '2px',
          transition: 'width 0.5s ease-out',
        }}
      />
    </div>
  </div>
)

export default GenerationProgress
