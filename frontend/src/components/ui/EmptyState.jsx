import { motion } from 'framer-motion';
import Button from './Button';

export default function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  actionLabel,
  className = ''
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        flex flex-col items-center justify-center
        p-12 text-center
        ${className}
      `}
    >
      {Icon && (
        <div className="mb-6 p-6 rounded-3xl bg-gradient-to-br from-primary-50 to-gold-50">
          <Icon className="w-12 h-12 text-primary-400" />
        </div>
      )}

      <h3 className="font-display text-xl font-bold text-ink mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-ink/60 max-w-sm mb-6">
          {description}
        </p>
      )}
      
      {action && actionLabel && (
        <Button onClick={action} variant="primary">
          {actionLabel}
        </Button>
      )}
    </motion.div>
  );
}
