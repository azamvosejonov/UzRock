import { Gamepad2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Game } from '../api/services'

interface GameGridProps {
  title: string
  count: number
  itemsPerRow?: number
  rows?: number
  games?: Game[]
  loading?: boolean
}

export default function GameGrid({ title, count, itemsPerRow = 10, rows = 2, games = [], loading }: GameGridProps) {
  const navigate = useNavigate()
  const displayGames = games.slice(0, itemsPerRow * rows)
  const placeholders = Array.from({ length: itemsPerRow * rows }, (_, i) => i)

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Gamepad2 size={18} color="#8b8bb0" />
          <span style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>{title}</span>
        </div>
        <span style={{ fontSize: '13px', color: '#6b8ce7', cursor: 'pointer' }}>{count} &gt;</span>
      </div>

      {loading && <div style={{ color: '#8b8bb0', fontSize: '13px' }}>Loading...</div>}

      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${itemsPerRow}, 1fr)`,
        gap: '10px'
      }}>
        {displayGames.length > 0 ? displayGames.map((game) => (
          <div key={game.id} onClick={() => navigate(`/games/${game.slug}`)} style={{ textAlign: 'center', cursor: 'pointer' }}>
            <div style={{
              aspectRatio: '1',
              background: '#1e3a8a',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '6px',
              overflow: 'hidden',
              position: 'relative',
              border: '2px solid #e5e7eb'
            }}>
              {game.icon_url ? (
                <img
                  src={game.icon_url}
                  alt={game.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <rect x="2" y="2" width="20" height="20" rx="4" fill="url(#grad)" />
                  <defs>
                    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#f59e0b" />
                      <stop offset="100%" stopColor="#fff" />
                    </linearGradient>
                  </defs>
                  <circle cx="10" cy="8" r="2" fill="white" />
                  <path d="M10 10l-2 4h3l-1 5 5-6h-3l2-3" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </div>
            <span style={{ fontSize: '11px', color: '#a0a0b8' }}>{game.name}</span>
          </div>
        )) : placeholders.map((i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{
              aspectRatio: '1',
              background: '#1e3a8a',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '6px',
              overflow: 'hidden',
              position: 'relative',
              border: '2px solid #e5e7eb'
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <rect x="2" y="2" width="20" height="20" rx="4" fill="url(#grad)" />
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" />
                    <stop offset="100%" stopColor="#fff" />
                  </linearGradient>
                </defs>
                <circle cx="10" cy="8" r="2" fill="white" />
                <path d="M10 10l-2 4h3l-1 5 5-6h-3l2-3" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span style={{ fontSize: '11px', color: '#a0a0b8' }}>Name</span>
          </div>
        ))}
      </div>
    </div>
  )
}
