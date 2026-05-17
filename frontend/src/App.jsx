import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import { DealProvider, useDealContext } from './context/DealContext'
import DealSidebar from './features/DealList/DealSidebar'
import ConfigForm from './features/ConfigForm/ConfigForm'
import DealView from './features/DealView/DealView'
import EmptyState from './features/DealList/EmptyState'
import './App.css'

const SIDEBAR_W = 260

const Layout = () => {
  const { fetchDealsList } = useDealContext()
  const [open, setOpen] = useState(true)

  useEffect(() => { fetchDealsList() }, [fetchDealsList])

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>
      {/* Sidebar — slides in/out */}
      <div style={{
        width: `${SIDEBAR_W}px`,
        flexShrink: 0,
        background: 'var(--surface)',
        borderRight: '1px solid var(--rule)',
        transform: open ? 'translateX(0)' : `translateX(-${SIDEBAR_W}px)`,
        transition: 'transform 0.3s ease',
        position: 'relative',
        zIndex: 10,
      }}>
        <DealSidebar />
      </div>

      {/* Main content — pushed by sidebar */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        marginLeft: open ? 0 : `-${SIDEBAR_W}px`,
        transition: 'margin-left 0.3s ease',
        position: 'relative',
      }}>
        {/* Hamburger button */}
        <div
          className={`hamburger${open ? ' change' : ''}`}
          onClick={() => setOpen(o => !o)}
          style={{
            position: 'fixed',
            top: '16px',
            left: open ? `${SIDEBAR_W + 14}px` : '14px',
            transition: 'left 0.3s ease',
            zIndex: 100,
          }}
        >
          <div className="bar1" />
          <div className="bar2" />
          <div className="bar3" />
        </div>

        <Outlet />
      </div>
    </div>
  )
}

const App = () => (
  <DealProvider>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<EmptyState />} />
          <Route path="/new" element={<ConfigForm />} />
          <Route path="/deals/:deal_id" element={<DealView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </DealProvider>
)

export default App
