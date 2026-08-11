import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Images, ScanFace, Zap, ShieldCheck, Sparkles,
  Heart, Camera, Users, Mail
} from 'lucide-react';
import GradientBlobs from '../components/ui/GradientBlobs';
import AccessCard from '../components/gallery/AccessCard';
import { saveGallerySession } from '../lib/gallerySession';

const STATS = [
  { icon: Images, value: '5,000+', label: 'Photos Delivered' },
  { icon: ScanFace, value: 'AI', label: 'Face Recognition' },
  { icon: Zap, value: '1 Second', label: 'Search Speed' },
  { icon: ShieldCheck, value: 'Secure', label: 'Cloud Storage' },
];

const FEATURES = [
  {
    icon: Camera,
    title: 'Effortless Delivery',
    description: 'Photographers upload hundreds of photos in minutes. Every wedding is its own private gallery.',
  },
  {
    icon: ScanFace,
    title: 'AI That Finds You',
    description: 'Once inside, upload a single selfie and instantly find every photo you appear in - no scrolling required.',
  },
  {
    icon: Heart,
    title: 'Crafted for Emotion',
    description: 'A gallery experience that feels as considered as the wedding itself - cinematic, warm, unforgettable.',
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  const handleUnlock = (session) => {
    saveGallerySession(session);
    navigate('/gallery');
  };

  return (
    <div>
      <section className="relative min-h-screen flex items-center overflow-hidden bg-gradient-to-br from-[#fdf8f3] via-[#f8ebd9] to-[#dcd0c0]">
        <GradientBlobs variant="hero" />

        {/* subtle bokeh dot texture */}
        <div
          className="absolute inset-0 opacity-40 pointer-events-none"
          style={{
            backgroundImage:
              'radial-gradient(2px 2px at 20% 30%, rgba(30,24,19,0.15) 0%, transparent 60%),' +
              'radial-gradient(2px 2px at 70% 65%, rgba(198,161,91,0.25) 0%, transparent 60%),' +
              'radial-gradient(1.5px 1.5px at 40% 80%, rgba(30,24,19,0.1) 0%, transparent 60%),' +
              'radial-gradient(2px 2px at 85% 20%, rgba(30,24,19,0.1) 0%, transparent 60%),' +
              'radial-gradient(1.5px 1.5px at 55% 45%, rgba(198,161,91,0.2) 0%, transparent 60%)',
          }}
        />

        {/* vignette */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#fdf8f3] via-transparent to-[#fdf8f3]/40 pointer-events-none" />

        <div className="relative w-full max-w-6xl mx-auto px-6 pt-32 pb-40 grid lg:grid-cols-2 gap-16 items-center">
          <div className="text-center lg:text-left">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100/60 border border-primary-200/50 text-ink/80 text-sm font-medium mb-8"
            >
              <Sparkles className="w-4 h-4 text-primary-600" />
              A Private Gallery for Every Wedding
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="font-display text-4xl md:text-5xl lg:text-6xl font-extrabold text-ink leading-[1.08] text-balance mb-8"
            >
              Every Wedding Has a Story.
              <span className="block mt-2 bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600 bg-clip-text text-transparent bg-200% animate-gradient-x">
                Relive Yours Beautifully.
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.6 }}
              className="text-lg text-ink/70 max-w-lg mx-auto lg:mx-0 text-balance"
            >
              No accounts, no public galleries. Just your Event Code and Password,
              shared privately by your photographer.
            </motion.p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <AccessCard onUnlock={handleUnlock} />
          </motion.div>
        </div>

        {/* Floating stats */}
        <div className="absolute bottom-0 left-0 right-0 translate-y-1/2 px-6">
          <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
            {STATS.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + i * 0.1, duration: 0.6 }}
                className="glass-dark rounded-2xl px-5 py-4 flex items-center gap-3 animate-float"
                style={{ animationDelay: `${i * 0.7}s` }}
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500/20 to-primary-600/10 flex items-center justify-center shrink-0">
                  <stat.icon className="w-5 h-5 text-primary-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-ink font-bold text-sm leading-tight">{stat.value}</p>
                  <p className="text-ink/60 text-xs leading-tight truncate">{stat.label}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- About ---------------- */}
      <section id="about" className="relative pt-40 pb-28 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-2xl mx-auto mb-16"
          >
            <p className="text-primary-600 font-semibold text-sm tracking-wide uppercase mb-3">
              About the Platform
            </p>
            <h2 className="font-display text-3xl md:text-4xl font-bold text-ink mb-4 text-balance">
              Photography deserves a gallery this considered
            </h2>
            <p className="text-ink/60 text-lg text-balance">
              Every wedding gets its own private, code-protected gallery -
              built for photographers who want delivery to feel as premium as the work itself.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-80px' }}
                transition={{ delay: i * 0.12, duration: 0.6 }}
                className="card-hover-lift bg-white rounded-3xl p-8 shadow-soft border border-primary-100/50"
              >
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-400 flex items-center justify-center mb-5 shadow-glow-primary">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-display text-xl font-bold text-ink mb-2">
                  {feature.title}
                </h3>
                <p className="text-ink/60 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <div className="luxury-divider max-w-4xl mx-auto" />

      {/* ---------------- Contact ---------------- */}
      <section id="contact" className="relative py-28 px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto text-center"
        >
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-gold-500 flex items-center justify-center mx-auto mb-6 shadow-glow-gold">
            <Users className="w-7 h-7 text-white" />
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold text-ink mb-4 text-balance">
            Lost your Event Code or Password?
          </h2>
          <p className="text-ink/60 text-lg mb-8 text-balance">
            Reach out and we'll help you get back into your gallery.
          </p>
          <a href="mailto:hello@shootatsight.com">
            <motion.span
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-white border border-primary-200 text-ink font-semibold shadow-soft cursor-pointer"
            >
              <Mail className="w-4 h-4" />
              Get in Touch
            </motion.span>
          </a>

          <p className="mt-10 text-sm text-ink/30">
            Are you a photographer?{' '}
            <Link to="/admin" className="text-ink/50 hover:text-primary-600 underline underline-offset-2 transition-colors">
              Sign in to your studio
            </Link>
          </p>
        </motion.div>
      </section>
    </div>
  );
}
