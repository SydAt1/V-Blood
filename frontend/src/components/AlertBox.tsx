import React from 'react';
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

interface Props {
  type?: 'warning' | 'error' | 'info' | 'disclaimer';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const AlertBox: React.FC<Props> = ({
  type = 'info',
  title,
  children,
  className = '',
}) => {
  const styles = {
    warning: {
      bg: 'bg-amber-950/40 border-amber-800 text-amber-200',
      icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
      titleColor: 'text-amber-300',
    },
    error: {
      bg: 'bg-rose-950/40 border-rose-800 text-rose-200',
      icon: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />,
      titleColor: 'text-rose-300',
    },
    info: {
      bg: 'bg-blue-950/30 border-blue-800 text-blue-200',
      icon: <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />,
      titleColor: 'text-blue-300',
    },
    disclaimer: {
      bg: 'bg-slate-900 border-slate-700 text-slate-300',
      icon: <ShieldAlert className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />,
      titleColor: 'text-slate-200',
    },
  }[type];

  return (
    <div className={`border rounded-lg p-3.5 flex gap-3 text-sm leading-relaxed ${styles.bg} ${className}`}>
      {styles.icon}
      <div className="flex-1 space-y-1">
        {title && <div className={`font-semibold ${styles.titleColor}`}>{title}</div>}
        <div className="text-xs leading-normal opacity-90">{children}</div>
      </div>
    </div>
  );
};
