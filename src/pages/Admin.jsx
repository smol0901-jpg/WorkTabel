import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Admin() {
  const [partners, setPartners] = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('partners')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    
    // Загружаем партнёров
    const { data: partnersData } = await supabase
      .from('users')
      .select('*')
      .eq('role', 'partner')
      .order('created_at', { ascending: false })
    setPartners(partnersData || [])

    // Загружаем все заказы
    const { data: ordersData } = await supabase
      .from('orders')
      .select('*, users(name, email)')
      .order('created_at', { ascending: false })
    setOrders(ordersData || [])

    setLoading(false)
  }

  async function togglePartnerStatus(partner) {
    await supabase
      .from('users')
      .update({ is_active: !partner.is_active })
      .eq('id', partner.id)
    
    loadData()
  }

  async function updateOrderStatus(orderId, status) {
    await supabase
      .from('orders')
      .update({ status })
      .eq('id', orderId)
    
    loadData()
  }

  async function sendToTelegram(order) {
    // Здесь будет логика отправки в Telegram группу
    alert('Отправка в Telegram группу (функция в разработке)')
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
        <h1 className="page-title">⚙️ Админ-панель</h1>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          <button 
            className={`btn ${activeTab === 'partners' ? 'btn-primary' : ''}`}
            onClick={() => setActiveTab('partners')}
          >
            Партнёры
          </button>
          <button 
            className={`btn ${activeTab === 'orders' ? 'btn-primary' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            Все заказы
          </button>
        </div>

        {loading ? (
          <div>Загрузка...</div>
        ) : activeTab === 'partners' ? (
          <div className="card">
            <h3 style={{ marginBottom: '16px' }}>Управление партнёрами</h3>
            {partners.length === 0 ? (
              <p style={{ color: 'var(--gray-500)' }}>Нет партнёров.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Имя</th>
                    <th>Email</th>
                    <th>Статус</th>
                    <th>Дата регистрации</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {partners.map(partner => (
                    <tr key={partner.id}>
                      <td>{partner.name || '—'}</td>
                      <td>{partner.email}</td>
                      <td>
                        <span className={`status-badge ${partner.is_active ? 'status-confirmed' : 'status-pending'}`}>
                          {partner.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td>{formatDate(partner.created_at)}</td>
                      <td>
                        <button 
                          className={`btn ${partner.is_active ? 'btn-danger' : 'btn-success'}`}
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                          onClick={() => togglePartnerStatus(partner)}
                        >
                          {partner.is_active ? 'Деактивировать' : 'Активировать'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className="card">
            <h3 style={{ marginBottom: '16px' }}>Все заказы</h3>
            {orders.length === 0 ? (
              <p style={{ color: 'var(--gray-500)' }}>Нет заказов.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Партнёр</th>
                    <th>Период</th>
                    <th>Режим</th>
                    <th>Человек</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map(order => {
                    const badge = getStatusBadge(order.status)
                    return (
                      <tr key={order.id}>
                        <td>
                          <div>{order.users?.name}</div>
                          <div style={{ fontSize: '12px', color: 'var(--gray-500)' }}>{order.users?.email}</div>
                        </td>
                        <td>{formatDate(order.start_date)} — {formatDate(order.end_date)}</td>
                        <td>{order.mode}</td>
                        <td>{order.person_count}</td>
                        <td>
                          <span className={`status-badge ${badge.class}`}>
                            {badge.text}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            {order.status === 'pending' && (
                              <button 
                                className="btn btn-success"
                                style={{ padding: '6px 12px', fontSize: '12px' }}
                                onClick={() => updateOrderStatus(order.id, 'confirmed')}
                              >
                                Подтвердить
                              </button>
                            )}
                            {order.status === 'confirmed' && (
                              <button 
                                className="btn btn-primary"
                                style={{ padding: '6px 12px', fontSize: '12px' }}
                                onClick={() => updateOrderStatus(order.id, 'sent')}
                              >
                                Отправить
                              </button>
                            )}
                            {order.status === 'sent' && (
                              <button 
                                className="btn"
                                style={{ padding: '6px 12px', fontSize: '12px', background: 'var(--gray-200)' }}
                                onClick={() => sendToTelegram(order)}
                              >
                                📤 В Telegram
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  )
}