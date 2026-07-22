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
        <div className="mb-6 p-6 rounded-2xl bg-slate-100 dark:bg-slate-800">
          <Icon className="w-12 h-12 text-slate-400 dark:text-slate-500" />
        </div>
      )}
      
      <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
        {title}
      </h3>
      
      {description && (
        <p className="text-slate-600 dark:text-slate-400 max-w-sm mb-6">
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
