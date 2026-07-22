import { motion } from 'framer-motion';

export default function Card({ 
  children, 
  className = '',
  hover = true,
  glass = false,
  ...props 
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : {}}
      className={`
        ${glass ? 'glass-card' : 'bg-white dark:bg-slate-800 rounded-2xl shadow-soft'}
        transition-all duration-300
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.div>
  );
}
