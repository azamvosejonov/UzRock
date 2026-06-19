import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { gameService, productService } from '../api/services'
import type { Game, Product } from '../api/services'
import { placeholderGames, placeholderProducts } from '../data/placeholders'

export default function GamePage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [game, setGame] = useState<Game | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    const fetchData = async () => {
      try {
        setLoading(true)
        const gameData = await gameService.get(slug)
        setGame(gameData)
        const productsData = await productService.list({
          game_id: gameData.id,
          page: 1,
          size: 20,
        })
        setProducts(productsData.items.length ? productsData.items : placeholderProducts.filter((p) => p.game_id === gameData.id))
      } catch (err) {
        const fallbackGame = placeholderGames.find((g) => g.slug === slug)
        if (fallbackGame) {
          setGame(fallbackGame)
          setProducts(placeholderProducts.filter((p) => p.game_id === fallbackGame.id))
        } else {
          setError('Game not found')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [slug])

  if (loading) {
    return (
      <div style={{ padding: '40px', color: '#8b8bb0', textAlign: 'center' }}>
        Loading game...
      </div>
    )
  }

  if (error || !game) {
    return (
      <div style={{ padding: '40px', color: '#ff6b6b', textAlign: 'center' }}>
        {error || 'Game not found'}
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <button
        onClick={() => navigate(-1)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'transparent',
          border: 'none',
          color: '#8b8bb0',
          cursor: 'pointer',
          fontSize: '14px',
          marginBottom: '16px',
        }}
      >
        <ArrowLeft size={18} />
        Back
      </button>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '32px',
          padding: '20px',
          background: '#16213e',
          borderRadius: '16px',
        }}
      >
        {game.icon_url ? (
          <img
            src={game.icon_url}
            alt={game.name}
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '16px',
              objectFit: 'cover',
            }}
          />
        ) : (
          <div
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '16px',
              background: '#1e3a8a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ color: '#fff', fontSize: '24px', fontWeight: 700 }}>
              {game.name.charAt(0)}
            </span>
          </div>
        )}
        <div>
          <h1
            style={{
              fontSize: '28px',
              color: '#fff',
              fontWeight: 700,
              marginBottom: '8px',
            }}
          >
            {game.name}
          </h1>
          {game.is_new && (
            <span
              style={{
                background: '#22c55e',
                color: '#fff',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              NEW
            </span>
          )}
        </div>
      </div>

      <h2
        style={{
          fontSize: '20px',
          color: '#fff',
          fontWeight: 600,
          marginBottom: '16px',
        }}
      >
        Products ({products.length})
      </h2>

      {products.length === 0 ? (
        <p style={{ color: '#8b8bb0', fontSize: '14px' }}>
          No products available for this game.
        </p>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '16px',
          }}
        >
          {products.map((product) => (
            <div
              key={product.id}
              onClick={() => navigate(`/products/${product.id}`)}
              style={{
                cursor: 'pointer',
                background: '#0d2847',
                borderRadius: '12px',
                overflow: 'hidden',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = 'translateY(-4px)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = 'translateY(0)')
              }
            >
              <img
                src={
                  product.images[0]?.image_url ||
                  'https://images.unsplash.com/photo-1612287230202-1ff1d56d7bdb?w=300&h=180&fit=crop'
                }
                alt={product.title}
                style={{
                  width: '100%',
                  height: '160px',
                  objectFit: 'cover',
                }}
              />
              <div style={{ padding: '12px' }}>
                <h3
                  style={{
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: 600,
                    marginBottom: '8px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {product.title}
                </h3>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <span
                    style={{
                      color: '#3b82f6',
                      fontWeight: 600,
                      fontSize: '14px',
                    }}
                  >
                    {product.price} UZS
                  </span>
                  {product.original_price && (
                    <span
                      style={{
                        fontSize: '12px',
                        color: '#6b7280',
                        textDecoration: 'line-through',
                      }}
                    >
                      {product.original_price}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
