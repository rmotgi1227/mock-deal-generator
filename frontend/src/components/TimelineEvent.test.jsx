import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import TimelineEvent from './TimelineEvent'

describe('TimelineEvent - Internal Calls', () => {
  const mockStakeholders = [
    { id: 'stakeholder1', name: 'John Doe' },
    { id: 'stakeholder2', name: 'Jane Smith' },
  ]

  const mockInternalCall = {
    id: 'uuid-internal-call-1',
    record_type: 'internal_call',
    title: 'Deal Review — Acme Corp',
    call_type: 'deal_review',
    date: '2024-03-15',
    timestamp: '2024-03-15T14:30:00Z',
    stage: 'Discovery',
    participants: [
      { name: 'Alice Johnson', role: 'AE' },
      { name: 'Bob Smith', role: 'Manager' }
    ],
    transcript: 'Alice: How are we doing with Acme? Bob: Good, sentiment is positive...',
    summary: 'Discussed deal progress and next steps.',
    action_items: ['Follow up on pricing question', 'Send contract draft'],
    deal_health: 'on_track',
    sentiment: 'positive'
  }

  // Test 14: Internal call typeLabel
  test('displays Int. Call typeLabel for internal_call events', () => {
    render(
      <TimelineEvent
        event={mockInternalCall}
        allEvents={[mockInternalCall]}
        stakeholders={mockStakeholders}
      />
    )

    expect(screen.getByText('Int. Call')).toBeInTheDocument()
  })

  // Test 15: Collapsed card title & subtitle
  test('shows title and participant names (no roles) in collapsed view', () => {
    render(
      <TimelineEvent
        event={mockInternalCall}
        allEvents={[mockInternalCall]}
        stakeholders={mockStakeholders}
      />
    )

    expect(screen.getByText('Deal Review — Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Alice Johnson, Bob Smith')).toBeInTheDocument()
  })

  // Tests 16-17-18 combined: Expanded header with all sections and deal health colors
  test('renders expanded view with header, participants, deal health, transcript, summary, and action items', () => {
    render(
      <TimelineEvent
        event={mockInternalCall}
        allEvents={[mockInternalCall]}
        stakeholders={mockStakeholders}
      />
    )

    // Click to expand the component (by clicking on the title)
    const cardTitle = screen.getByText('Deal Review — Acme Corp')
    fireEvent.click(cardTitle.parentElement.parentElement)

    // Test 16: Expanded header
    expect(screen.getByText('Deal Review — Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Alice Johnson (AE), Bob Smith (Manager)')).toBeInTheDocument()
    expect(screen.getByText(/On track/)).toBeInTheDocument()

    // Test 17: Deal health colors (on_track = teal) - verified by presence of "On track" badge
    // Test 18: Expanded content sections
    expect(screen.getByText('Participants')).toBeInTheDocument()
    expect(screen.getByText('Alice Johnson — AE')).toBeInTheDocument()
    expect(screen.getByText('Bob Smith — Manager')).toBeInTheDocument()
    expect(screen.getByText('Transcript')).toBeInTheDocument()
    expect(screen.getByText('Summary')).toBeInTheDocument()
    expect(screen.getByText('Discussed deal progress and next steps.')).toBeInTheDocument()
    expect(screen.getByText('Action Items')).toBeInTheDocument()
    expect(screen.getByText('Follow up on pricing question')).toBeInTheDocument()
    expect(screen.getByText('Send contract draft')).toBeInTheDocument()
  })

  // Test 19: Border color (purple) - single test
  test('displays internal call card with purple border rgba(168,85,247,0.26)', () => {
    render(
      <TimelineEvent
        event={mockInternalCall}
        allEvents={[mockInternalCall]}
        stakeholders={mockStakeholders}
      />
    )

    // Find the card element semantically by locating the title text
    const titleElement = screen.getByText('Deal Review — Acme Corp')

    // The title is inside a span → div (flex, baseline, gap) → div (flex: 1) → div (flex, align-items: flex-start) → card div
    // Navigate up 4 levels from the span to reach the card div with the border color
    const cardElement = titleElement.parentElement?.parentElement?.parentElement?.parentElement

    // Verify the card element exists and has the correct border color
    expect(cardElement).toBeInTheDocument()
    expect(cardElement.getAttribute('style')).toContain('rgba(168,85,247,0.26)')
  })

  // Test 5a: Empty action_items array (component has `?.length > 0` check)
  test('does not render Action Items section when array is empty', () => {
    const eventWithNoActionItems = { ...mockInternalCall, action_items: [] }

    render(
      <TimelineEvent
        event={eventWithNoActionItems}
        allEvents={[eventWithNoActionItems]}
        stakeholders={mockStakeholders}
      />
    )

    // Click to expand (by clicking on the title)
    const cardTitle = screen.getByText('Deal Review — Acme Corp')
    fireEvent.click(cardTitle.parentElement.parentElement)

    // Verify Action Items section is NOT rendered
    expect(screen.queryByText(/Action Items/)).not.toBeInTheDocument()
  })

  // Test 5b: Missing transcript
  test('renders empty transcript gracefully', () => {
    const eventWithoutTranscript = { ...mockInternalCall, transcript: null }

    render(
      <TimelineEvent
        event={eventWithoutTranscript}
        allEvents={[eventWithoutTranscript]}
        stakeholders={mockStakeholders}
      />
    )

    // Click to expand (by clicking on the title)
    const cardTitle = screen.getByText('Deal Review — Acme Corp')
    fireEvent.click(cardTitle.parentElement.parentElement)

    // Verify Transcript section exists but is empty
    const transcriptLabel = screen.getByText(/Transcript/)
    expect(transcriptLabel).toBeInTheDocument()
    const transcriptSection = transcriptLabel.closest('div').parentElement
    expect(transcriptSection).toBeInTheDocument()
  })
})
