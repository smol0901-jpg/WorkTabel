import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [mode, setMode] = useState('5/2')
  const [personCount, setPersonCount] = useState(1)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadOrders()
  }, [])

  async function loadOrders() {
    setLoading(true)
    const { data: { user } } = await supabase.auth.getUser()
    
    const { data } = await supabase
      .from('orders')
      .select('*, users(name)')
      .eq('user_id', user?.id)
      .order('created_at', { ascending: false })
    
    setOrders(data || [])
    setLoading(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setMessage('')

    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      const { error } = await supabase.from('orders').insert([{
        user_id: user.id,
        start_date: startDate,
        end_date: endDate,
        person_count: personCount,
        mode,
        status: 'pending'
      }])

      if (error) throw error
      
      setMessage('Заявка отправлена! Ожидайте подтверждения.')
      setShowForm(false)
      loadOrders()
    } catch (err) {
      setMessage('Ошибка: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  function getStatusBadge(status) {
    const badges = {
      pending: { text: 'Ожидает', class: 'status-pending' },
      confirmed: { text: 'Подтверждено', class: 'status-confirmed' },
      sent: { text: 'Отправлено', class: 'status-sent' }
    }
    return badges[status] || badges.pending
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('ru')
  }

  return (
    <div className="page">
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h1 className="page-title" style={{ marginBottom: 0 }}>📝 Заказы</h1>
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Отмена' : '+ Новый заказ'}
          </button>
        </div>

        {showForm && (
          <div className="card" style={{ marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Создать заказ</h3>
            
            {message && (
              <div className={`alert ${message.includes('Ошибка') ? 'alert-error' : 'alert-success'}`}>
                {message}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Режим меню</label>
                <select value={mode} onChange={(e) => setMode(e.target.value)}>
                  <option value="5/2">5/2 (10 дней)</option>
                  <option value="7/0">7/0 (14 дней)</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label>Дата начала</label>
                  <input 
                    type="date" 
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Дата окончания</label>
                  <input 
                    type="date" 
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Количество человек</label>
                <input 
                  type="number" 
                  value={personCount}
                  onChange={(e) => setPersonCount(parseInt(e.target.value))}
                  min="1"
                  max="100"
                  required
                />
              </div>

              <button type="submit" className="btn btn-success" disabled={submitting}>
                {submitting ? 'Отправка...' : 'Отправить заявку'}
              </button>
            </form>
          </div>
        )}

        {loading ? (
          <div>Загрузка...</div>
        ) : orders.length === 0 ? (
          <div className="card">
            <p style={{ color: 'var(--gray-500)' }}>У вас пока нет заказов.</p>
          </div>
        ) : (
          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>Период</th>
                  <th>Режим</th>
                  <th>Человек</th>
                  <th>Статус</th>
                  <th>Дата заявки</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => {
                  const badge = getStatusBadge(order.status)
                  return (
                    <tr key={order.id}>
                      <td>{formatDate(order.start_date)} — {formatDate(order.end_date)}</td>
                      <td>{order.mode}</td>
                      <td>{order.person_count}</td>
                      <td>
                        <span className={`status-badge ${badge.class}`}>
                          {badge.text}
                        </span>
                      </td>
                      <td>{formatDate(order.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}