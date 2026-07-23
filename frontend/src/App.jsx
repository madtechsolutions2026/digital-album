import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import GradientBlobs from './components/ui/GradientBlobs';
import HomePage from './pages/HomePage';
import AdminPage from './pages/AdminPage';
import GalleryPage from './pages/GalleryPage';

function AppShell() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      <Navbar />

      {isHome ? (
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      ) : (
        <>
          <GradientBlobs />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-32 pb-20">
            <Routes>
              <Route path="/gallery" element={<GalleryPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </main>
        </>
      )}

      <footer className="relative py-10 border-t border-primary-100/60">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-sm text-ink/50">
            Powered by InsightFace AI · Built with FastAPI & React
          </p>
          <p className="text-xs text-ink/30 mt-1.5">
            Crafted with care for photographers and the couples they capture.
          </p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}

export default App;
