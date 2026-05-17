import React, { createContext, useState, useCallback } from 'react'
import { dealApi } from '../utils/api'

// Create context
export const DealContext = createContext()

// Provider component
export const DealProvider = ({ children }) => {
  const [currentDeal, setCurrentDeal] = useState(null)
  const [dealsList, setDealsList] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Generate new deal with retry logic (3 attempts)
  const generateDeal = useCallback(async (config) => {
    setLoading(true)
    setError(null)

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const response = await dealApi.generate(config)
        setCurrentDeal(response.deal)
        setLoading(false)
        return response // Return full response with deal_id for navigation
      } catch (err) {
        if (attempt === 3) {
          const errorMsg = err.response?.data?.detail || err.message || 'Generation failed'
          setError(errorMsg)
          setLoading(false)
          throw err
        }
        // Continue to next attempt if not the last one
      }
    }
  }, [])

  // Fetch all deals for sidebar
  const fetchDealsList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await dealApi.listDeals()
      setDealsList(response.deals || [])
      setLoading(false)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load deals'
      setError(errorMsg)
      setLoading(false)
    }
  }, [])

  // Load single deal by ID
  const loadDeal = useCallback(async (dealId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await dealApi.getDeal(dealId)
      setCurrentDeal(response.deal)
      setLoading(false)
      return response.deal
    } catch (err) {
      const errorMsg = err.response?.status === 404 ? 'Deal not found' : err.response?.data?.detail || 'Failed to load deal'
      setError(errorMsg)
      setLoading(false)
      throw err
    }
  }, [])

  // Delete deal by ID
  const deleteDeal = useCallback(async (dealId) => {
    // Optimistic update: remove from UI immediately
    const previousList = dealsList
    setDealsList(dealsList.filter(d => d.deal_id !== dealId))

    try {
      await dealApi.deleteDeal(dealId)
      // Refetch list on success
      await fetchDealsList()
    } catch (err) {
      // Restore list on error
      setDealsList(previousList)
      const errorMsg = err.response?.data?.detail || 'Failed to delete deal'
      setError(errorMsg)
    }
  }, [dealsList, fetchDealsList])

  const value = {
    currentDeal,
    setCurrentDeal,
    dealsList,
    setDealsList,
    loading,
    setLoading,
    error,
    setError,
    generateDeal,
    fetchDealsList,
    loadDeal,
    deleteDeal
  }

  return (
    <DealContext.Provider value={value}>
      {children}
    </DealContext.Provider>
  )
}

// Custom hook to use context
export const useDealContext = () => {
  const context = React.useContext(DealContext)
  if (!context) {
    throw new Error('useDealContext must be used within DealProvider')
  }
  return context
}
