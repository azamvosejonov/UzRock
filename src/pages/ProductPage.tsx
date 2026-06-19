import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Star, Eye, ShoppingCart, Truck, Zap } from 'lucide-react'
import { productService } from '../api/services'
import type { Product } from '../api/services'
import { placeholderProducts } from '../data/placeholders'

export default function ProductPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    const fetchProduct = async () => {
      try {
        setLoading(true)
        const data = await productService.get(id)
        setProduct(data)
      } catch (err) {
        const fallback = placeholderProducts.find((p) => p.id === id)
        if (fallback) {
          setProduct(fallback)
        } else {
          setError('Product not found')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchProduct()
  }, [id])

  if (loading) {
    return (
      <div style={{ padding: '40px', color: '#8b8bb0', textAlign: 'center' }}>
        Loading product...
      </div>
    )
  }

  if (error || !product) {
    return (
      <div style={{ padding: '40px', color: '#ff6b6b', textAlign: 'center' }}>
        {error || 'Product not found'}
      </div>
    )
  }

  const discount =
    product.original_price && parseFloat(product.original_price) > parseFloat(product.price)
      ? Math.round(
          ((parseFloat(product.original_price) - parseFloat(product.price)) /
            parseFloat(product.original_price)) *
            100
        )
      : product.discount_percent

  const mainImage =
    product.images.length > 0
      ? product.images[0].image_url
      : 'https://images.unsplash.com/photo-1612287230202-1ff1d56d7bdb?w=600&h=400&fit=crop'

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
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '40px',
        }}
      >
        <div>
          <div
            style={{
              background: '#0d2847',
              borderRadius: '16px',
              overflow: 'hidden',
              aspectRatio: '16/10',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <img
              src={mainImage}
              alt={product.title}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
          {product.images.length > 1 && (
            <div
              style={{
                display: 'flex',
                gap: '10px',
                marginTop: '12px',
                overflowX: 'auto',
              }}
            >
              {product.images.map((img) => (
                <img
                  key={img.id}
                  src={img.image_url}
                  alt=""
                  style={{
                    width: '80px',
                    height: '60px',
                    objectFit: 'cover',
                    borderRadius: '8px',
                    border: '2px solid #2a2a40',
                    flexShrink: 0,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        <div>
          <h1
            style={{
              fontSize: '28px',
              color: '#fff',
              marginBottom: '16px',
              fontWeight: 700,
            }}
          >
            {product.title}
          </h1>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '24px',
              flexWrap: 'wrap',
            }}
          >
            <span
              style={{
                fontSize: '26px',
                color: '#3b82f6',
                fontWeight: 700,
              }}
            >
              {product.price} UZS
            </span>
            {product.original_price && (
              <span
                style={{
                  fontSize: '18px',
                  color: '#6b7280',
                  textDecoration: 'line-through',
                }}
              >
                {product.original_price} UZS
              </span>
            )}
            {!!discount && (
              <span
                style={{
                  background: '#ef4444',
                  color: '#fff',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 600,
                }}
              >
                -{discount}%
              </span>
            )}
          </div>

          {product.is_auto_delivery && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '16px',
                color: '#22c55e',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              <Zap size={18} />
              Auto Delivery
            </div>
          )}

          {product.delivery_method && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '16px',
                color: '#a0a0b8',
                fontSize: '14px',
              }}
            >
              <Truck size={18} />
              {product.delivery_method}
              {product.delivery_details && `: ${product.delivery_details}`}
            </div>
          )}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '20px',
              marginBottom: '24px',
              color: '#8b8bb0',
              fontSize: '14px',
            }}
          >
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Eye size={16} />
              {product.views} views
            </span>
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Star size={16} />
              {product.review_count} reviews
            </span>
          </div>

          <div
            style={{
              background: '#16213e',
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '24px',
            }}
          >
            <h3
              style={{
                color: '#fff',
                fontSize: '14px',
                fontWeight: 600,
                marginBottom: '8px',
              }}
            >
              Description
            </h3>
            <p
              style={{
                color: '#a0a0b8',
                lineHeight: 1.6,
                fontSize: '14px',
                whiteSpace: 'pre-wrap',
              }}
            >
              {product.description || 'No description available.'}
            </p>
          </div>

          {product.dynamic_attributes &&
            Object.keys(product.dynamic_attributes).length > 0 && (
              <div
                style={{
                  background: '#16213e',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '24px',
                }}
              >
                <h3
                  style={{
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: 600,
                    marginBottom: '8px',
                  }}
                >
                  Details
                </h3>
                {Object.entries(product.dynamic_attributes).map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '6px 0',
                      borderBottom: '1px solid #2a2a40',
                      fontSize: '14px',
                    }}
                  >
                    <span style={{ color: '#8b8bb0' }}>{key}</span>
                    <span style={{ color: '#fff' }}>{String(value)}</span>
                  </div>
                ))}
              </div>
            )}

          <button
            style={{
              width: '100%',
              padding: '14px',
              background: '#2a6db5',
              color: '#fff',
              borderRadius: '10px',
              border: 'none',
              fontSize: '16px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <ShoppingCart size={18} />
            Buy Now
          </button>
        </div>
      </div>
    </div>
  )
}
