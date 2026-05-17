import React from 'react'

// 6-node sentiment arc visualization per spec
const SentimentArc = ({ metadata }) => {
  const stages = metadata.sentiment_arc
  const stageNames = ['Prospecting', 'Discovery', 'Demo', 'Evaluation', 'Negotiation', 'Closed']

  // Sentiment to color mapping per Mock_Deal_REQUIREMENTS.md Section 9
  const sentimentColors = {
    positive: 'bg-green-500',
    neutral: 'bg-gray-400',
    concerned: 'bg-amber-500',
    negative: 'bg-red-500'
  }

  const sentimentLabels = {
    positive: '😊 Positive',
    neutral: '😐 Neutral',
    concerned: '😟 Concerned',
    negative: '😞 Negative'
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">Sentiment Arc</h2>

      {/* SVG arc with connecting lines */}
      <div className="bg-white rounded-lg p-8 overflow-x-auto">
        <svg width="100%" height="300" className="min-w-max" viewBox="0 0 1200 300">
          {/* Connecting lines */}
          {stages.map((stage, i) => {
            if (i < stages.length - 1) {
              const x1 = 100 + i * 180
              const x2 = 100 + (i + 1) * 180
              const nextSentiment = stages[i + 1].sentiment

              return (
                <line
                  key={`line-${i}`}
                  x1={x1}
                  y1="150"
                  x2={x2}
                  y2="150"
                  stroke={sentimentColors[nextSentiment]}
                  strokeWidth="3"
                  opacity="0.6"
                />
              )
            }
            return null
          })}

          {/* Nodes */}
          {stages.map((stage, i) => {
            const x = 100 + i * 180
            const sentimentColor = sentimentColors[stage.sentiment]

            return (
              <g key={`node-${i}`}>
                {/* Node circle */}
                <circle
                  cx={x}
                  cy="150"
                  r="30"
                  className={sentimentColor}
                  opacity="0.8"
                />

                {/* Stage name below */}
                <text
                  x={x}
                  y="200"
                  textAnchor="middle"
                  className="text-sm font-medium"
                  fill="#1f2937"
                >
                  {stageNames[i]}
                </text>

                {/* Sentiment label above */}
                <text
                  x={x}
                  y="110"
                  textAnchor="middle"
                  className="text-xs"
                  fill="#374151"
                >
                  {sentimentLabels[stage.sentiment]}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}

export default SentimentArc
