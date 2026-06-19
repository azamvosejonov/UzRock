import { Star } from 'lucide-react'

export default function ReplenishSection() {
  return (
    <div style={{
      margin: '40px 24px 24px',
      background: 'rgba(40, 40, 60, 0.6)',
      borderRadius: '16px',
      padding: '20px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: '20px',
      flexWrap: 'wrap',
      border: '1px solid #2a2a45'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        minWidth: '160px'
      }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: '#3a3a55',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Star size={18} color="#ffd700" />
        </div>
        <div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Replenish Steam</div>
          <div style={{ fontSize: '12px', color: '#6b8ce7', cursor: 'pointer' }}>Enter promocode &gt;</div>
        </div>
      </div>

      <button style={{
        padding: '10px 20px',
        borderRadius: '10px',
        border: '1px solid #3a3a55',
        background: '#2a2a40',
        color: '#8b8bb0',
        fontSize: '13px',
        cursor: 'pointer'
      }}>Log into Steam</button>

      <div style={{
        flex: 1,
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '16px',
        alignItems: 'center',
        minWidth: '280px'
      }}>
        <div>
          <div style={{ fontSize: '11px', color: '#8b8bb0', marginBottom: '4px' }}>Amount</div>
          <div style={{
            background: '#2a2a40',
            padding: '10px 16px',
            borderRadius: '10px',
            fontSize: '14px',
            fontWeight: 500,
            border: '1px solid #3a3a55',
            minWidth: '120px'
          }}>100.000 UZS</div>
        </div>
        <button style={{
          padding: '12px 28px',
          borderRadius: '10px',
          border: 'none',
          background: '#2a6db5',
          color: '#fff',
          fontSize: '14px',
          fontWeight: 500,
          cursor: 'pointer',
          marginTop: '16px'
        }}>Pay 100.000 UZS</button>
      </div>
    </div>
  )
}
