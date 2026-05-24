import React, { useMemo } from 'react'

const formatTime = (timestamp) =>
  new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

const SENDER_COLORS = {
  AE: '#a78bfa', SDR: '#60a5fa', Manager: '#f472b6',
  SE: '#34d399', Legal: '#fb923c', CS: '#facc15', Rep: '#a78bfa',
}

const SlackMessage = ({ message, isReply }) => {
  const color = SENDER_COLORS[message.sender] || 'var(--accent, #a78bfa)'
  const displayName = message.sender_name || message.sender
  const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      paddingLeft: isReply ? '32px' : '0',
      marginTop: isReply ? '6px' : '0',
    }}>
      <div style={{
        width: '28px', height: '28px', borderRadius: '5px',
        background: color, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '11px', fontWeight: '700', flexShrink: 0,
      }}>
        {initials}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '3px' }}>
          <span style={{ fontSize: '13px', fontWeight: '600', color: color }}>{displayName}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: '500' }}>{message.sender}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{formatTime(message.timestamp)}</span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: '1.55', margin: 0 }}>{message.body}</p>
      </div>
    </div>
  )
}

const SlackThread = ({ parent, replies }) => (
  <div style={{
    background: 'var(--surface)',
    border: '1px solid var(--rule)',
    borderRadius: '8px',
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  }}>
    <SlackMessage message={parent} isReply={false} />
    {replies.length > 0 && (
      <div style={{
        borderLeft: '2px solid var(--rule)',
        marginLeft: '13px',
        paddingLeft: '0',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        marginTop: '4px',
      }}>
        {replies.map(r => (
          <SlackMessage key={r.message_id} message={r} isReply={true} />
        ))}
      </div>
    )}
  </div>
)

export default function SlackView({ deal }) {
  const channels = useMemo(() =>
    (deal.events || [])
      .filter(e => e.record_type === 'slack_channel')
      .map(e => e.channel)
      .filter(Boolean),
    [deal.events]
  )

  if (channels.length === 0) {
    return <p style={{ fontSize: '13px', color: 'var(--text-dim)', fontStyle: 'italic' }}>No Slack channels for this deal.</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {channels.map(channel => {
        const messages = channel.messages || []
        // Build thread groups: top-level messages with their replies nested
        const byId = Object.fromEntries(messages.map(m => [m.message_id, m]))
        const threads = []
        const seen = new Set()
        messages.forEach(msg => {
          if (msg.is_thread_reply) return
          const replies = messages.filter(m => m.is_thread_reply && m.thread_parent_id === msg.message_id)
          threads.push({ parent: msg, replies })
          seen.add(msg.message_id)
          replies.forEach(r => seen.add(r.message_id))
        })
        // Orphaned replies (parent not found) — show as standalone
        messages.forEach(msg => {
          if (!seen.has(msg.message_id)) threads.push({ parent: msg, replies: [] })
        })

        return (
          <div key={channel.channel_id}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
              <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                #{channel.name}
              </span>
              <div style={{ flex: 1, height: '1px', background: 'var(--rule)' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {threads.map(({ parent, replies }) => (
                <SlackThread key={parent.message_id} parent={parent} replies={replies} />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
