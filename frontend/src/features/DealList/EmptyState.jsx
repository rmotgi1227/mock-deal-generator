import React from 'react'
import { useNavigate } from 'react-router-dom'

// Empty state when no deal is selected
const EmptyState = () => {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center justify-center h-full bg-gradient-to-b from-gray-50 to-white">
      <div className="text-center">
        <div className="mb-4 text-6xl">📋</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No deal selected</h2>
        <p className="text-gray-600 mb-6">Click "New Deal" in the sidebar to generate a synthetic B2B sales deal, or select an existing deal.</p>
        <button
          onClick={() => navigate('/new')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
        >
          Create New Deal
        </button>
      </div>
    </div>
  )
}

export default EmptyState
