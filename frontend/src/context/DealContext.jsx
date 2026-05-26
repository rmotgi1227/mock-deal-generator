import React, { createContext, useState, useCallback, useRef } from 'react'
import { dealApi, BASE_URL, getAuthHeaders } from '../utils/api'

export const DealContext = createContext()

export const DealProvider = ({ children }) => {
  const [currentDeal, setCurrentDeal] = useState(null)
  const [dealsList, setDealsList] = useState([])
  const [loading, setLoading] = useState(false)
  const [listLoading, setListLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState(null)
  const [listError, setListError] = useState(null)
  const [detailError, setDetailError] = useState(null)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationStep, setGenerationStep] = useState('')
  const [bulkProgress, setBulkProgress] = useState({ completed: 0, failed: 0, total: 0 })
  const [bulkLoading, setBulkLoading] = useState(false)
  const abortRef = useRef(null)

  // Generate deal with real-time SSE progress streaming
  const generateDealStream = useCallback(async (config) => {
    setLoading(true)
    setError(null)
    setGenerationProgress(0)
    setGenerationStep('Starting...')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${BASE_URL}/api/generate-stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(config),
        signal: controller.signal,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'progress') {
            setGenerationProgress(event.progress)
            setGenerationStep(event.message)
          } else if (event.type === 'complete') {
            setGenerationProgress(100)
            setGenerationStep('Complete!')
            setCurrentDeal(event.deal)
            setLoading(false)
            return event // {deal_id, filename, deal}
          } else if (event.type === 'error') {
            throw new Error(event.message)
          }
        }
      }

      throw new Error('Stream ended without completion event')
    } catch (err) {
      if (err.name === 'AbortError') {
        setLoading(false)
        setGenerationProgress(0)
        setGenerationStep('')
        return
      }
      const errorMsg = err.message || 'Generation failed'
      setError(errorMsg)
      setLoading(false)
      setGenerationProgress(0)
      setGenerationStep('')
      throw err
    }
  }, [])

  // Generate series with real-time SSE progress streaming
  const seriesGenerateStream = useCallback(async (seriesConfig) => {
    setLoading(true)
    setError(null)
    setGenerationProgress(0)
    setGenerationStep('Starting...')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${BASE_URL}/api/generate-series-stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(seriesConfig),
        signal: controller.signal,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'progress') {
            setGenerationProgress(event.progress)
            setGenerationStep(event.message)
          } else if (event.type === 'complete') {
            setGenerationProgress(100)
            setGenerationStep('Complete!')
            setCurrentDeal(event.deal)
            setLoading(false)
            return event
          } else if (event.type === 'error') {
            throw new Error(event.message)
          }
        }
      }

      throw new Error('Stream ended without completion event')
    } catch (err) {
      if (err.name === 'AbortError') {
        setLoading(false)
        setGenerationProgress(0)
        setGenerationStep('')
        return
      }
      const errorMsg = err.message || 'Generation failed'
      setError(errorMsg)
      setLoading(false)
      setGenerationProgress(0)
      setGenerationStep('')
      throw err
    }
  }, [])

  // Fetch all deals for sidebar
  const fetchDealsList = useCallback(async () => {
    setListLoading(true)
    setListError(null)
    try {
      const response = await dealApi.listDeals()
      setDealsList(response.data.deals || [])
      setListLoading(false)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load deals'
      setListError(errorMsg)
      setListLoading(false)
    }
  }, [])

  // Load single deal by ID
  const loadDeal = useCallback(async (dealId) => {
    setDetailLoading(true)
    setDetailError(null)
    try {
      const response = await dealApi.getDeal(dealId)
      setCurrentDeal(response.data.deal)
      setDetailLoading(false)
      return response.data.deal
    } catch (err) {
      const errorMsg = err.response?.status === 404 ? 'Deal not found' : err.response?.data?.detail || 'Failed to load deal'
      setDetailError(errorMsg)
      setDetailLoading(false)
      throw err
    }
  }, [])

  const cancelGeneration = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const bulkGenerateStream = useCallback(async (count, overrides = null) => {
    setBulkLoading(true)
    setBulkProgress({ completed: 0, failed: 0, total: count })

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const response = await fetch(`${BASE_URL}/api/bulk-generate-stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ count, overrides }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'deal_complete') {
            setBulkProgress(prev => ({ ...prev, completed: event.completed }))
          } else if (event.type === 'deal_error') {
            setBulkProgress(prev => ({ ...prev, failed: prev.failed + 1 }))
          } else if (event.type === 'bulk_complete') {
            setBulkProgress({ completed: event.completed, failed: event.failed, total: event.total })
            setBulkLoading(false)
            await fetchDealsList()
            return event
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setBulkLoading(false)
        setBulkProgress({ completed: 0, failed: 0, total: 0 })
        return
      }
      setBulkLoading(false)
      throw err
    }
  }, [fetchDealsList])

  // Delete deal by ID
  const deleteDeal = useCallback(async (dealId) => {
    const previousList = dealsList
    setDealsList(dealsList.filter(d => d.deal_id !== dealId))

    try {
      await dealApi.deleteDeal(dealId)
      await fetchDealsList()
    } catch (err) {
      setDealsList(previousList)
      const errorMsg = err.response?.data?.detail || 'Failed to delete deal'
      setListError(errorMsg)
    }
  }, [dealsList, fetchDealsList])

  const value = {
    bulkProgress,
    bulkLoading,
    bulkGenerateStream,
    currentDeal,
    setCurrentDeal,
    dealsList,
    setDealsList,
    loading,
    setLoading,
    listLoading,
    detailLoading,
    error,
    setError,
    listError,
    setListError,
    detailError,
    setDetailError,
    generationProgress,
    generationStep,
    generateDealStream,
    seriesGenerateStream,
    cancelGeneration,
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

export const useDealContext = () => {
  const context = React.useContext(DealContext)
  if (!context) {
    throw new Error('useDealContext must be used within DealProvider')
  }
  return context
}
