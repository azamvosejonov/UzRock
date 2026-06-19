import { api } from './client'

export interface Game {
  id: string
  name: string
  slug: string
  category_id: string
  icon_url: string | null
  is_new: boolean
}

export interface Category {
  id: string
  name: string
  slug: string
}

export interface ProductImage {
  id: string
  image_url: string
  sort_order: number
}

export interface Product {
  id: string
  seller_id: string
  game_id: string
  subcategory_id: string
  title: string
  description: string | null
  price: string
  original_price: string | null
  discount_percent: number | null
  delivery_method: string | null
  delivery_details: string | null
  is_auto_delivery: boolean
  dynamic_attributes: Record<string, unknown> | null
  views: number
  review_count: number
  is_active: boolean
  is_highlighted: boolean
  images: ProductImage[]
  created_at: string
}

export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface UserOut {
  id: string
  username: string
  email: string
  avatar_url: string | null
  balance: string
  held_balance: string
  is_seller: boolean
  is_admin: boolean
  is_on_vacation: boolean
  auto_reply: string | null
  total_sales: number
  response_time: number
  rating: number
  last_online: string
  created_at: string
}

export interface UserPublicProfile {
  id: string
  username: string
  avatar_url: string | null
  is_seller: boolean
  is_on_vacation: boolean
  total_sales: number
  response_time: number
  rating: number
  last_online: string
  created_at: string
}

export const authService = {
  register: (payload: UserCreate) => api<Token>('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload: UserLogin) => api<Token>('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => api<UserOut>('/auth/me'),
}

export const gameService = {
  list: (params?: { category_id?: string; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.category_id) query.append('category_id', params.category_id)
    if (params?.search) query.append('search', params.search)
    return api<Game[]>(`/games/?${query.toString()}`)
  },
  get: (slug: string) => api<Game>(`/games/${slug}`),
}

export const categoryService = {
  list: () => api<Category[]>('/categories/'),
  get: (slug: string) => api<Category>(`/categories/${slug}`),
  games: (slug: string) => api<Game[]>(`/categories/${slug}/games`),
}

export const productService = {
  list: (params?: {
    game_id?: string
    subcategory_id?: string
    seller_id?: string
    min_price?: number
    max_price?: number
    is_auto_delivery?: boolean
    has_discount?: boolean
    is_highlighted?: boolean
    search?: string
    sort_by?: string
    page?: number
    size?: number
  }) => {
    const query = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          query.append(key, String(value))
        }
      })
    }
    return api<PagedResponse<Product>>(`/products/?${query.toString()}`)
  },
  get: (id: string) => api<Product>(`/products/${id}`),
}

export const userService = {
  get: (username: string) => api<UserPublicProfile>(`/users/${username}`),
  products: (username: string, page = 1, size = 20) =>
    api<PagedResponse<Product>>(`/users/${username}/products?page=${page}&size=${size}`),
  reviews: (username: string, page = 1, size = 20) =>
    api<PagedResponse<unknown>>(`/users/${username}/reviews?page=${page}&size=${size}`),
}
