import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface BentoCardProps {
  title?: string;
  subtitle?: string;
  badge?: string;
  badgeColor?: 'peach' | 'steel' | 'success' | 'warning' | 'danger';
  icon?: LucideIcon;
  colSpan?: 'col-span-1' | 'col-span-2' | 'col-span-3' | 'col-span-4';
  rowSpan?: 'row-span-1' | 'row-span-2';
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  glow?: 'peach' | 'steel' | 'none';
}

export const BentoCard: React.FC<BentoCardProps> = ({
  title,
  subtitle,
  badge,
  badgeColor = 'steel',
  icon: Icon,
  colSpan = 'col-span-1',
  rowSpan = 'row-span-1',
  headerAction,
  children,
  className = '',
  glow = 'none',
}) => {
  const getBadgeClass = () => {
    switch (badgeColor) {
      case 'peach':
        return 'bento-badge-peach';
      case 'success':
        return 'bento-badge-success';
      case 'warning':
        return 'bento-badge-warning';
      case 'danger':
        return 'bento-badge-danger';
      case 'steel':
      default:
        return 'bento-badge-steel';
    }
  };

  const getGlowBg = () => {
    if (glow === 'peach') return 'before:absolute before:-top-24 before:-right-24 before:w-48 before:h-48 before:bg-[#FAD4C0]/10 before:rounded-full before:blur-3xl before:pointer-events-none';
    if (glow === 'steel') return 'before:absolute before:-top-24 before:-right-24 before:w-48 before:h-48 before:bg-[#80A1C1]/10 before:rounded-full before:blur-3xl before:pointer-events-none';
    return '';
  };

  return (
    <div
      className={`bento-card bento-border-highlight ${colSpan} ${rowSpan} ${getGlowBg()} ${className}`}
    >
      {(title || Icon || badge || headerAction) && (
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="w-8 h-8 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-[#80A1C1] shadow-inner">
                <Icon className="w-4 h-4" />
              </div>
            )}
            <div>
              {title && <h3 className="text-sm font-semibold text-white tracking-tight">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {badge && <span className={getBadgeClass()}>{badge}</span>}
            {headerAction}
          </div>
        </div>
      )}
      <div className="relative z-10">{children}</div>
    </div>
  );
};
