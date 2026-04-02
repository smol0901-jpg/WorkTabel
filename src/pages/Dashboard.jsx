import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [stats, setStats] = useState({
    pending: 0,
    confirmed: 0,
    sent: 0
  })
  const [todayMenu, setTodayMenu] = useState(null)
  const [userName, setUserName] = useState('')

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    const today = new Date().toISOString().split('T')[0]
    
    // Загружаем меню на сегодня
    const { data: menu } = await supabase
      .from('menus')
      .select('*')
      .eq('date', today)
      .single()
    setTodayMenu(menu)

    // Загружаем статистику заказов
    const { count: pending } = await supabase
      .from('orders')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'pending')

    const { count: confirmed } = await supabase
      .from('orders')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'confirmed')

    const { count: sent } = await supabase
      .from('orders')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'sent')

    setStats({ pending: pending || 0, confirmed: confirmed || 0, sent: sent || 0 })

    // Получаем имя пользователя
    const { data: { user } } = await supabase.auth.getUser()
    if (user?.user_metadata?.name) {
      setUserName(user.user_metadata.name)
    }
  }

  const today = new Date()
  const dayNames = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
  const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

  return (
    <div className="page">
      <div className="container">
        <h1 className="page-title">
          Добро пожаловать, {userName || 'Partner'}!
        </h1>

        <div style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '16px',
          padding: '32px',
          color: 'white',
          marginBottom: '32px'
        }}>
          <div style={{ fontSize: '48px', fontWeight: '700' }}>
            {today.getDate()} {monthNames[today.getMonth()]}
          </div>
          <div style={{ fontSize: '18px', opacity: 0.9 }}>
            {dayNames[today.getDay()]}
          </div>
        </div>

        <div className="menu-grid" style={{ marginBottom: '32px' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--warning)' }}>
              {stats.pending}
            </div>
            <div style={{ color: 'var(--gray-500)', marginTop: '8px' }}>Ожидают</div>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--success)' }}>
              {stats.confirmed}
            </div>
            <div style={{ color: 'var(--gray-500)', marginTop: '8px' }}>Подтверждено</div>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--primary)' }}>
              {stats.sent}
            </div>
            <div style={{ color: 'var(--gray-500)', marginTop: '8px' }}>Отправлено</div>
          </div>
        </div>

        {todayMenu && (
          <div className="card">
            <h2 style={{ marginBottom: '16px' }}>🍽 Меню на сегодня</h2>
            <div className="menu-item">
              <div className="menu-item-label">Завтрак</div>
              <div className="menu-item-value">{todayMenu.breakfast || '—'}</div>
            </div>
            <div className="menu-item">
              <div className="menu-item-label">Обед</div>
              <div className="menu-item-value">{todayMenu.lunch || '—'}</div>
            </div>
            <div className="menu-item">
              <div className="menu-item-label">Ужин</div>
              <div className="menu-item-value">{todayMenu.dinner || '—'}</div>
            </div>
          </div>
        )}

        <div style={{ marginTop: '24px', display: 'flex', gap: '16px' }}>
          <Link to="/menu" className="btn btn-primary">Посмотреть меню</Link>
          <Link to="/orders" className="btn btn-success">Создать заказ</Link>
        </div>
      </div>
    </div>
  )
}