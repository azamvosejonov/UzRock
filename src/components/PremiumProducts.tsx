import { Gamepad2, Star, LayoutGrid } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Product } from '../api/services'

interface PremiumProductsProps {
  products?: Product[]
  loading?: boolean
}

export default function PremiumProducts({ products = [], loading }: PremiumProductsProps) {
  const navigate = useNavigate()
  const placeholders = Array.from({ length: 10 }, (_, i) => i)

  return (
    <div style={{ margin: '32px 24px 0' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '16px'
      }}>
        <Gamepad2 size={18} color="#8b8bb0" />
        <span style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Premium products</span>
      </div>

      {loading && <div style={{ color: '#8b8bb0', fontSize: '13px', marginBottom: '12px' }}>Loading...</div>}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '16px'
      }}>
        {products.length > 0 ? products.map((product) => (
          <div key={product.id} onClick={() => navigate(`/products/${product.id}`)} style={{ cursor: 'pointer' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <LayoutGrid size={14} color="#fff" />
              </div>
              <span style={{ fontSize: '13px', color: '#c0c0d0' }}>
                {product.title.length > 20 ? product.title.slice(0, 20) + '...' : product.title}
              </span>
            </div>

            <div style={{
              background: '#0d2847',
              borderRadius: '12px',
              overflow: 'hidden',
              aspectRatio: '16/10',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              marginBottom: '10px'
            }}>
              <img
                src={product.images.length > 0 ? product.images[0].image_url : 'https://images.unsplash.com/photo-1612287230202-1ff1d56d7bdb?w=300&h=180&fit=crop'}
                alt={product.title}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', color: '#3b82f6', fontWeight: 500 }}>
                {product.price} UZS
              </span>
              {product.original_price && (
                <span style={{ fontSize: '12px', color: '#6b7280', textDecoration: 'line-through' }}>
                  {product.original_price}
                </span>
              )}
            </div>

            <p style={{
              fontSize: '12px',
              color: '#9ca3af',
              lineHeight: 1.4,
              marginBottom: '8px'
            }}>
              {product.description ? product.description.slice(0, 60) : product.title}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ display: 'flex' }}>
                {[1, 2, 3].map((s) => (
                  <Star key={s} size={12} color="#3b82f6" fill="#3b82f6" />
                ))}
                {[4, 5].map((s) => (
                  <Star key={s} size={12} color="#6b7280" />
                ))}
              </div>
              <span style={{ fontSize: '11px', color: '#6b7280' }}>
                {product.review_count}
              </span>
            </div>
          </div>
        )) : placeholders.map((i) => (
          <div key={i}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <LayoutGrid size={14} color="#fff" />
              </div>
              <span style={{ fontSize: '13px', color: '#c0c0d0' }}>Name</span>
            </div>

            <div style={{
              background: '#0d2847',
              borderRadius: '12px',
              overflow: 'hidden',
              aspectRatio: '16/10',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              marginBottom: '10px'
            }}>
              <img
                src="https://images.unsplash.com/photo-1612287230202-1ff1d56d7bdb?w=300&h=180&fit=crop"
                alt="Product"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', color: '#3b82f6', fontWeight: 500 }}>120,000 UZS</span>
              <span style={{ fontSize: '12px', color: '#6b7280', textDecoration: 'line-through' }}>160,000</span>
            </div>

            <p style={{
              fontSize: '12px',
              color: '#9ca3af',
              lineHeight: 1.4,
              marginBottom: '8px'
            }}>This is the name for the card of video games.</p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ display: 'flex' }}>
                {[1, 2, 3].map((s) => (
                  <Star key={s} size={12} color="#3b82f6" fill="#3b82f6" />
                ))}
                {[4, 5].map((s) => (
                  <Star key={s} size={12} color="#6b7280" />
                ))}
              </div>
              <span style={{ fontSize: '11px', color: '#6b7280' }}>76767</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
