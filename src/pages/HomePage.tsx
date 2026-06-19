import { useEffect, useState } from 'react'
import HeroBanner from '../components/HeroBanner'
import ReplenishSection from '../components/ReplenishSection'
import GameGrid from '../components/GameGrid'
import PremiumProducts from '../components/PremiumProducts'
import { gameService, categoryService, productService } from '../api/services'
import type { Game, Product, Category } from '../api/services'
import { placeholderCategories, placeholderGames, placeholderProducts } from '../data/placeholders'

export default function HomePage() {
  const [games, setGames] = useState<Game[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loadingGames, setLoadingGames] = useState(true)
  const [loadingProducts, setLoadingProducts] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [gamesData, categoriesData, productsData] = await Promise.all([
          gameService.list(),
          categoryService.list(),
          productService.list({ page: 1, size: 10 }),
        ])
        setGames(gamesData.length ? gamesData : placeholderGames)
        setCategories(categoriesData.length ? categoriesData : placeholderCategories)
        setProducts(productsData.items.length ? productsData.items : placeholderProducts)
      } catch (err) {
        console.error('Failed to fetch data, using placeholders:', err)
        setGames(placeholderGames)
        setCategories(placeholderCategories)
        setProducts(placeholderProducts)
      } finally {
        setLoadingGames(false)
        setLoadingProducts(false)
      }
    }

    fetchData()
  }, [])

  const gamesCategory = categories.find((c) => c.slug === 'games')
  const appsCategory = categories.find((c) => c.slug === 'apps')
  const mobileCategory = categories.find((c) => c.slug === 'mobile-games')

  const gamesList = gamesCategory ? games.filter((g) => g.category_id === gamesCategory.id) : games.slice(0, 20)
  const appsList = appsCategory ? games.filter((g) => g.category_id === appsCategory.id) : games.slice(0, 10)
  const mobileList = mobileCategory ? games.filter((g) => g.category_id === mobileCategory.id) : games.slice(0, 14)

  return (
    <>
      <HeroBanner />
      <ReplenishSection />
      <div style={{ display: 'flex', gap: '24px', margin: '24px 24px 0' }}>
        <div style={{ flex: 2 }}>
          <GameGrid
            title="Games"
            count={gamesList.length}
            itemsPerRow={10}
            rows={2}
            games={gamesList}
            loading={loadingGames}
          />
        </div>
        <div style={{ flex: 1 }}>
          <GameGrid
            title="Apps"
            count={appsList.length}
            itemsPerRow={5}
            rows={2}
            games={appsList}
            loading={loadingGames}
          />
        </div>
      </div>
      <div style={{ margin: '24px 24px 0' }}>
        <GameGrid
          title="Mobile Games"
          count={mobileList.length}
          itemsPerRow={14}
          rows={1}
          games={mobileList}
          loading={loadingGames}
        />
      </div>
      <PremiumProducts products={products} loading={loadingProducts} />
    </>
  )
}
