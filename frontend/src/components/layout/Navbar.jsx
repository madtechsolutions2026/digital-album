import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Gallery', path: '/gallery' },
  { label: 'About', path: '/#about' },
  { label: 'Contact', path: '/#contact' },
];

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleAnchorClick = (e, path) => {
    if (!path.startsWith('/#')) return;
    e.preventDefault();
    const id = path.slice(2);

    if (location.pathname !== '/') {
      navigate('/');
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
      }, 150);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex justify-center pt-4 px-4">
      <motion.nav
        initial={{ y: -24, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-5xl glass-card rounded-full px-3 py-2.5 flex items-center justify-between"
      >
        <Link to="/" className="flex flex-col items-start pl-2 shrink-0 gap-0.5">
          <img 
            src="https://pub-53f55a87e6f64c51862dbd0fa933eee1.r2.dev/common/logo_1.webp" 
            alt="Shoot @ Sight" 
            className="h-9 w-auto object-contain"
          />
          <span className="text-[6.5px] tracking-[0.18em] font-bold text-ink/50 uppercase leading-none font-sans select-none">
            WEDDING PHOTOGRAPHERS & FILMMAKERS
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.label}
                to={item.path}
                onClick={(e) => handleAnchorClick(e, item.path)}
                className="relative px-4 py-2 rounded-full text-sm font-medium text-ink/70 hover:text-ink transition-colors"
              >
                {isActive && (
                  <motion.div
                    layoutId="navActivePill"
                    className="absolute inset-0 bg-primary-50 rounded-full -z-10"
                    transition={{ type: 'spring', duration: 0.5 }}
                  />
                )}
                {item.label}
              </Link>
            );
          })}
        </div>

        <Link to="/gallery" className="shrink-0">
          <motion.span
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-gradient-to-r from-primary-600 to-primary-500 text-white text-sm font-semibold shadow-glow-primary cursor-pointer"
          >
            Find My Photos
          </motion.span>
        </Link>
      </motion.nav>
    </div>
  );
}
