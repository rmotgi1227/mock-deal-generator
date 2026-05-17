import React, { useState } from 'react'

// Deal header with company info, badges, and expandable config
const DealHeader = ({ deal }) => {
  const [showConfig, setShowConfig] = useState(false)
  const metadata = deal.metadata

  // Format date range
  const startDate = new Date(metadata.deal_start_date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric'
  })
  const endDate = new Date(metadata.deal_end_date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric'
  })
  const durationDays = Math.round(
    (new Date(metadata.deal_end_date) - new Date(metadata.deal_start_date)) / (1000 * 60 * 60 * 24)
  )

  // Outcome color
  const outcomeColor = metadata.config.deal_outcome === 'closed_won'
    ? 'bg-green-100 text-green-800'
    : 'bg-red-100 text-red-800'

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          {metadata.company.name}
        </h1>

        {/* Badge row */}
        <div className="flex flex-wrap gap-2 mb-4">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            {metadata.config.deal_size}
          </span>
          <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
            {metadata.config.industry}
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${outcomeColor}`}>
            {metadata.config.deal_outcome === 'closed_won' ? '✓ Won' : '✗ Lost'}
          </span>
          <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
            {metadata.config.complexity.charAt(0).toUpperCase() + metadata.config.complexity.slice(1)}
          </span>
        </div>

        {/* Date row */}
        <p className="text-gray-600 text-sm">
          Start: {startDate} · Close: {endDate} · Duration: {durationDays} days
        </p>
      </div>

      {/* Collapsible config panel */}
      <button
        onClick={() => setShowConfig(!showConfig)}
        className="text-blue-600 hover:text-blue-700 font-medium text-sm mb-4"
      >
        {showConfig ? '▼' : '▶'} Configuration
      </button>

      {showConfig && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-2 gap-4">
            {[
              ['Industry', metadata.config.industry],
              ['Deal Size', metadata.config.deal_size],
              ['Sales Cycle', `${metadata.config.sales_cycle_length_days} days`],
              ['Starting Sentiment', metadata.config.starting_sentiment],
              ['Ending Sentiment', metadata.config.ending_sentiment],
              ['Outcome', metadata.config.deal_outcome],
              ['Champion Entry', metadata.config.champion_entry],
              ['Main Objection', metadata.config.main_objection],
              ['Buyer Urgency', metadata.config.buyer_urgency],
              ['Calls', metadata.config.num_calls],
              ['Emails/Stage', metadata.config.emails_per_stage],
              ['Stakeholders', metadata.config.num_stakeholders],
              ['Complexity', metadata.config.complexity],
              ['Sales Rep', `${metadata.sales_rep.name} (${metadata.sales_rep.title})`],
            ].map(([label, value]) => (
              <div key={label}>
                <div className="text-xs font-medium text-gray-600 mb-1">{label}</div>
                <div className="text-sm text-gray-900">{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DealHeader
