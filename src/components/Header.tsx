import { Clock, RefreshCw, MessageCircle, User, Search } from 'lucide-react'

export default function Header() {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      background: 'rgba(30, 30, 46, 0.95)',
      backdropFilter: 'blur(10px)',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      borderBottom: '1px solid #2a2a40'
    }}>
      <div style={{
        fontSize: '22px',
        fontWeight: 700,
        color: '#fff',
        letterSpacing: '-0.5px'
      }}>Logo</div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        flex: 1,
        maxWidth: '600px',
        margin: '0 auto',
        background: '#2a2a40',
        borderRadius: '10px',
        padding: '8px 14px',
        gap: '8px'
      }}>
        <Clock size={18} color="#8b8bb0" />
        <Search size={18} color="#8b8bb0" />
        <input
          type="text"
          placeholder="Search games and apps"
          style={{
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#fff',
            fontSize: '14px',
            flex: 1,
            width: '100%'
          }}
        />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          background: '#2a6db5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
        </div>
        <RefreshCw size={22} color="#8b8bb0" />
        <MessageCircle size={22} color="#8b8bb0" />
        <User size={22} color="#8b8bb0" />
      </div>
    </header>
  )
}
