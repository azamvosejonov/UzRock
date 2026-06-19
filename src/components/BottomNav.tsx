import { Home, Hand, FileText, Settings, LayoutGrid, Code } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function BottomNav() {
  const navigate = useNavigate()

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'rgba(30, 30, 46, 0.98)',
      backdropFilter: 'blur(10px)',
      borderTop: '1px solid #2a2a40',
      padding: '10px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '24px',
      zIndex: 100
    }}>
      <button onClick={() => navigate('/')} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}>
        <Home size={22} color="#8b8bb0" />
      </button>
      <Hand size={22} color="#8b8bb0" />
      <FileText size={22} color="#8b8bb0" />

      <button style={{
        padding: '8px 16px',
        borderRadius: '8px',
        border: 'none',
        background: '#2a6db5',
        color: '#fff',
        fontSize: '13px',
        fontWeight: 500,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}>
        Ask to edit
      </button>

      <Settings size={22} color="#8b8bb0" />
      <LayoutGrid size={22} color="#8b8bb0" />
      <Code size={22} color="#8b8bb0" />
    </nav>
  )
}
