import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, LayoutGrid, Settings } from 'lucide-react'
import AdminPage from './pages/AdminPage'
import GalleryPage from './pages/GalleryPage'

function Navigation() {
  const location = useLocation()

  const navItems = [
    { path: '/gallery', label: 'Gallery', icon: LayoutGrid },
    { path: '/admin', label: 'Admin', icon: Settings },
  ]

  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-40">
      <div className="glass-card px-2 py-2 flex items-center gap-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
          const Icon = item.icon
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className="relative"
            >
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  transition-colors duration-200
                  ${isActive
                    ? 'text-primary-600 dark:text-primary-400'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{item.label}</span>
              </motion.div>
              
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-primary-100 dark:bg-primary-900/30 rounded-lg -z-10"
                  transition={{ type: 'spring', duration: 0.5 }}
                />
              )}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        {/* Hero Header */}
        <header className="relative overflow-hidden pt-24 pb-16 px-4">
          {/* Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-accent-50 to-slate-50 dark:from-primary-950 dark:via-accent-950 dark:to-slate-950 opacity-50" />
          
          {/* Content */}
          <div className="relative max-w-4xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium mb-6"
            >
              <Sparkles className="w-4 h-4" />
              AI-Powered Digital Album
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 dark:text-slate-100 mb-6 text-balance"
            >
              Your Wedding Memories,
              <span className="block mt-2 bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                Beautifully Organized
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-8 text-balance"
            >
              Upload hundreds of photos, find anyone instantly with AI face recognition,
              and share beautiful galleries with couples and guests.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-600 dark:text-slate-400"
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span>Fast Upload</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-primary-500" />
                <span>AI Face Search</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-accent-500" />
                <span>Beautiful Galleries</span>
              </div>
            </motion.div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-12">
          <Routes>
            <Route path="/" element={<GalleryPage />} />
            <Route path="/gallery" element={<GalleryPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="mt-24 py-12 border-t border-slate-200 dark:border-slate-800">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Powered by InsightFace AI • Built with FastAPI & React
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
              © 2024 Digital Album. Crafted with care for photographers and couples.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App

