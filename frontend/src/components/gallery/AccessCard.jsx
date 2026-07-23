import { useState } from 'react';
import { motion } from 'framer-motion';
import { KeyRound, Lock, Eye, EyeOff, ArrowRight, AlertCircle, Heart } from 'lucide-react';
import { galleryAPI } from '../../lib/api';

export default function AccessCard({ onUnlock, className = '' }) {
  const [accessCode, setAccessCode] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!accessCode.trim() || !password.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await galleryAPI.access(accessCode.trim(), password);
      onUnlock(response.data.data);
    } catch (err) {
      setError(
        err.response?.data?.message || 'Incorrect event code or password. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`relative rounded-4xl bg-gradient-to-br from-primary-600 via-primary-500 to-gold-500 p-1 shadow-glow-primary ${className}`}
    >
      <div className="rounded-[calc(2rem-4px)] bg-white/95 backdrop-blur-xl px-7 py-9 sm:px-10 sm:py-11">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-gold-500 flex items-center justify-center mx-auto mb-5 shadow-glow-primary">
          <Heart className="w-7 h-7 text-white" fill="white" />
        </div>

        <h2 className="font-display text-2xl font-bold text-ink text-center mb-2">
          Access Your Wedding
        </h2>
        <p className="text-ink/60 text-center text-sm mb-8 text-balance">
          Enter the Event Code and Password your photographer shared with you
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary-400" />
            <input
              type="text"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
              placeholder="EVENT CODE"
              autoCapitalize="characters"
              className="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-primary-100 bg-primary-50/40 text-ink font-semibold tracking-widest placeholder:font-normal placeholder:tracking-normal placeholder:text-ink/30 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary-400" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full pl-11 pr-11 py-3.5 rounded-2xl border border-primary-100 bg-primary-50/40 text-ink placeholder:text-ink/30 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent transition-all"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-ink/30 hover:text-ink/60 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-rose-600 text-sm bg-rose-50 rounded-xl px-3.5 py-2.5"
            >
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </motion.div>
          )}

          <motion.button
            type="submit"
            disabled={loading || !accessCode.trim() || !password.trim()}
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: loading ? 1 : 0.98 }}
            className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-primary-600 to-primary-500 text-white font-semibold shadow-glow-primary disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full"
              />
            ) : (
              <>
                Unlock Gallery
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  );
}
