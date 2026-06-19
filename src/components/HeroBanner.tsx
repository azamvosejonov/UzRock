import { Star } from 'lucide-react'

export default function HeroBanner() {
  const bgUrl = 'https://images.unsplash.com/photo-1592155931584-901ac15763e3?w=1200&h=300&fit=crop'

  return (
    <div style={{ position: 'relative' }}>
      <div style={{
        height: '220px',
        background: `linear-gradient(to bottom, rgba(26,26,46,0.2), #1a1a2e), url(${bgUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        borderRadius: '0 0 16px 16px',
        margin: '0 16px',
        position: 'relative'
      }}>
        <div style={{
          position: 'absolute',
          bottom: '-20px',
          left: '16px',
          display: 'flex',
          gap: '8px'
        }}>
          {[1, 2, 3].map((i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(40, 40, 60, 0.9)',
              backdropFilter: 'blur(10px)',
              padding: '8px 14px',
              borderRadius: '20px',
              fontSize: '13px',
              color: '#c0c0d0',
              border: '1px solid #3a3a55'
            }}>
              <Star size={14} color="#ffd700" />
              Name
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
