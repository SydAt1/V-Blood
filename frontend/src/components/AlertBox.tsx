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
      container: 'bg-[#F9F4EB] border-[#D6C4A5] text-[#543815]',
      icon: <AlertTriangle className="w-4 h-4 text-[#8C5A20] shrink-0 mt-0.5" />,
      titleColor: 'text-[#6C4412]',
      tag: 'CAUTION // PARAMETRIC ADVISORY',
    },
    error: {
      container: 'bg-[#F9ECEB] border-[#DCB0AC] text-[#6B201A]',
      icon: <AlertCircle className="w-4 h-4 text-[#9B332B] shrink-0 mt-0.5" />,
      titleColor: 'text-[#7D221C]',
      tag: 'ERROR // VALIDATION EXCEPTION',
    },
    info: {
      container: 'bg-[#EFF4F7] border-[#BCD0DC] text-[#224458]',
      icon: <Info className="w-4 h-4 text-[#2E5875] shrink-0 mt-0.5" />,
      titleColor: 'text-[#244B64]',
      tag: 'NOTE // SYSTEM STATE',
    },
    disclaimer: {
      container: 'bg-[#F2ECE1] border-[#C9BFAD] text-[#3A3F3A]',
      icon: <ShieldAlert className="w-4 h-4 text-[#5F675E] shrink-0 mt-0.5" />,
      titleColor: 'text-[#1F221F]',
      tag: 'PROTOCOL // RESEARCH BOUNDARY',
    },
  }[type];

  return (
    <div
      className={`border rounded-none p-3.5 flex gap-3 text-xs leading-relaxed shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)] ${styles.container} ${className}`}
    >
      {styles.icon}
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between gap-2">
          {title && <span className={`font-semibold tracking-tight text-xs ${styles.titleColor}`}>{title}</span>}
          <span className="font-mono text-[9px] uppercase tracking-wider text-[#757D74] opacity-80">
            {styles.tag}
          </span>
        </div>
        <div className="text-[11.5px] leading-relaxed opacity-95">{children}</div>
      </div>
    </div>
  );
};
