function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export function Card({ children, className, glow, ...props }) {
  return (
    <div
      className={cn(
        'rounded-2xl bg-[#111] border border-white/10 relative overflow-hidden',
        'transition-all duration-300',
        glow && 'hover:border-white/20',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function GlowCard({ children, color = 'blue', className, ...props }) {
  const glowColors = {
    blue: 'bg-blue-500/10 group-hover:bg-blue-500/20',
    purple: 'bg-purple-500/10 group-hover:bg-purple-500/20',
    green: 'bg-green-500/10 group-hover:bg-green-500/20',
    rose: 'bg-rose-500/10 group-hover:bg-rose-500/20',
  };

  return (
    <div
      className={cn(
        'p-8 rounded-3xl bg-gradient-to-br from-white/5 to-transparent border border-white/10',
        'relative overflow-hidden group transition-all duration-500',
        className
      )}
      {...props}
    >
      <div className={cn('absolute top-0 right-0 w-32 h-32 blur-[50px] rounded-full transition duration-500', glowColors[color])} />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
