import { motion } from 'framer-motion';

export default function ProgressBar({ value, max = 100, label, showPercentage = true }) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="w-full space-y-2">
      {(label || showPercentage) && (
        <div className="flex items-center justify-between text-sm">
          {label && (
            <span className="text-slate-600 dark:text-slate-400 font-medium">
              {label}
            </span>
          )}
          {showPercentage && (
            <span className="text-slate-900 dark:text-slate-100 font-semibold">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      
      <div className="relative h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
        
        {/* Shimmer effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
      </div>
    </div>
  );
}
