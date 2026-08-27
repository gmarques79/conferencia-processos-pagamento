import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  AlertOctagon,
  MinusCircle 
} from 'lucide-react';
import { CertificateStatus, DocumentStatus } from '../types';

interface StatusBadgeProps {
  status: CertificateStatus | DocumentStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3.5 py-1.5 text-sm font-semibold',
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5 mr-1',
    md: 'w-4 h-4 mr-1.5',
    lg: 'w-5 h-5 mr-2',
  };

  switch (status) {
    case 'OK':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 ${sizeClasses[size]}`}
        >
          <CheckCircle2 className={`${iconSizes[size]} text-emerald-600`} />
          Regular / OK
        </span>
      );

    case 'AUSENTE':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-red-50 text-red-700 border border-red-200 ${sizeClasses[size]}`}
        >
          <XCircle className={`${iconSizes[size]} text-red-600`} />
          Ausente
        </span>
      );

    case 'VENCIDA':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-red-50 text-red-700 border border-red-200 ${sizeClasses[size]}`}
        >
          <AlertOctagon className={`${iconSizes[size]} text-red-600`} />
          Vencida
        </span>
      );

    case 'CNPJ_DIVERGENTE':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-red-50 text-red-700 border border-red-200 ${sizeClasses[size]}`}
        >
          <XCircle className={`${iconSizes[size]} text-red-600`} />
          CNPJ Divergente
        </span>
      );

    case 'VALIDADE_NAO_IDENTIFICADA':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-amber-50 text-amber-700 border border-amber-200 ${sizeClasses[size]}`}
        >
          <HelpCircle className={`${iconSizes[size]} text-amber-600`} />
          Validade Indeterminada
        </span>
      );

    case 'REVISAR_MANUALMENTE':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-amber-50 text-amber-700 border border-amber-200 ${sizeClasses[size]}`}
        >
          <AlertTriangle className={`${iconSizes[size]} text-amber-600`} />
          Revisar Manualmente
        </span>
      );

    case 'NAO_APLICAVEL':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-slate-100 text-slate-600 border border-slate-200 ${sizeClasses[size]}`}
        >
          <MinusCircle className={`${iconSizes[size]} text-slate-500`} />
          Não Aplicável
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center rounded-full bg-slate-100 text-slate-700 border border-slate-200 ${sizeClasses[size]}`}
        >
          {status}
        </span>
      );
  }
};
