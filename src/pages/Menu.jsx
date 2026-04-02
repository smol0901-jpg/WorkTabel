import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Menu() {
  const [menus, setMenus] = useState([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState('5/2')
  const [filter, setFilter] = useState('all') // all, today, tomorrow

  useEffect(() => {
    loadMenus()
  }, [mode])

  async function loadMenus() {
    setLoading(true)
    const { data, error } = await supabase
      .from('menus')
      .select('*')
      .eq('mode', mode)
      .order('date')
      .limit(14)
    
    if (!error) setMenus(data || [])
    setLoading(false)
  }

  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  const todayStr = today.toISOString().split('T')[0]
  const tomorrowStr = tomorrow.toISOString().split('T')[0]

  const filteredMenus = menus.filter(m => {
    if (filter === 'today') return m.date === todayStr
    if (filter === 'tomorrow') return m.date === tomorrowStr
    return true
  })

  function formatDate(dateStr) {
    const date = new Date(dateStr)
    const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
    const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    return `${days[date.getDay()]}, ${date.getDate()} ${months[date.getMonth()]}`
  }

  return (
    <div className="page">
      <div className="container">
        <h1 className="page-title">📋 Меню</h1>

        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
          <div>
            <label style={{ marginRight: '8px', fontWeight: 500 }}>Режим:</label>
            <select 
              value={mode} 
              onChange={(e) => setMode(e.target.value)}
              style={{ width: 'auto' }}
            >
              <option value="5/2">5/2 (10 дней)</option>
              <option value="7/0">7/0 (14 дней)</option>
            </select>
          </div>
          <div>
            <label style={{ marginRight: '8px', fontWeight: 500 }}>Показать:</label>
            <select 
              value={filter} 
              onChange={(e) => setFilter(e.target.value)}
              style={{ width: 'auto' }}
            >
              <option value="all">Всё меню</option>
              <option value="today">Сегодня</option>
              <option value="tomorrow">Завтра</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div>Загрузка...</div>
        ) : filteredMenus.length === 0 ? (
          <div className="card">
            <p style={{ color: 'var(--gray-500)' }}>
              Меню пока не загружено. Обратитесь к администратору.
            </p>
          </div>
        ) : (
          <div className="menu-grid">
            {filteredMenus.map(menu => (
              <div 
                key={menu.id} 
                className="menu-day"
                style={{ 
                  borderLeft: menu.date === todayStr ? '4px solid var(--success)' : 
                               menu.date === tomorrowStr ? '4px solid var(--warning)' : 'none'
                }}
              >
                <h3>
                  {formatDate(menu.date)}
                  {menu.date === todayStr && <span style={{ marginLeft: '8px', color: 'var(--success)' }}>Сегодня</span>}
                  {menu.date === tomorrowStr && <span style={{ marginLeft: '8px', color: 'var(--warning)' }}>Завтра</span>}
                </h3>
                <div className="menu-item">
                  <div className="menu-item-label">🌅 Завтрак</div>
                  <div className="menu-item-value">{menu.breakfast || '—'}</div>
                </div>
                <div className="menu-item">
                  <div className="menu-item-label">☀️ Обед</div>
                  <div className="menu-item-value">{menu.lunch || '—'}</div>
                </div>
                <div className="menu-item">
                  <div className="menu-item-label">🌙 Ужин</div>
                  <div className="menu-item-value">{menu.dinner || '—'}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}