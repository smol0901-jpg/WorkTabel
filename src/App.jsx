import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { createClient } from '@supabase/supabase-js'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Menu from './pages/Menu'
import Orders from './pages/Orders'
import Admin from './pages/Admin'
import { supabase } from './lib/supabase'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    checkUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null)
      if (session?.user) checkIsAdmin(session.user.id)
      else setIsAdmin(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  async function checkUser() {
    const { data: { session } } = await supabase.auth.getSession()
    setUser(session?.user || null)
    if (session?.user) checkIsAdmin(session.user.id)
    setLoading(false)
  }

  async function checkIsAdmin(userId) {
    const { data } = await supabase
      .from('users')
      .select('role')
      .eq('id', userId)
      .single()
    setIsAdmin(data?.role === 'admin')
  }

  if (loading) return <div className="container" style={{paddingTop: '100px'}}>Загрузка...</div>

  return (
    <BrowserRouter>
      {user && (
        <header className="header">
          <div className="container header-content">
            <div className="logo">🍽 WorkTable</div>
            <nav className="nav">
              <Link to="/">Главная</Link>
              <Link to="/menu">Меню</Link>
              <Link to="/orders">Заказы</Link>
              {isAdmin && <Link to="/admin">Админ</Link>}
              <a href="#" onClick={() => supabase.auth.signOut()}>Выход</a>
            </nav>
          </div>
        </header>
      )}
      <Routes>
        <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
        <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="/menu" element={user ? <Menu /> : <Navigate to="/login" />} />
        <Route path="/orders" element={user ? <Orders /> : <Navigate to="/login" />} />
        <Route path="/admin" element={user && isAdmin ? <Admin /> : <Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App