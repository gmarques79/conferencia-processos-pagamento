import React, { useState } from 'react';
import { 
  ExternalLink, 
  Calendar, 
  Layers, 
  ChevronDown, 
  ChevronUp 
} from 'lucide-react';
import { CertificateResult, CertificateStatus } from '../types';
import { StatusBadge } from './StatusBadge';

interface CertificateCardProps {
  certificate: CertificateResult;
  onOverride: (status: CertificateStatus, found: boolean, notes?: string) => Promise<void>;
  isUpdating: boolean;
}

export const CertificateCard: React.FC<CertificateCardProps> = ({
  certificate,
  onOverride,
  isUpdating,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const getCardBorder = () => {
    switch (certificate.status) {
      case 'OK':
        return 'border-emerald-200 hover:border-emerald-300 bg-white';
      case 'AUSENTE':
        return 'border-red-200 hover:border-red-300 bg-red-50/20';
      case 'VENCIDA':
      case 'CNPJ_DIVERGENTE':
        return 'border-red-200 hover:border-red-300 bg-red-50/20';
      case 'VALIDADE_NAO_IDENTIFICADA':
      case 'REVISAR_MANUALMENTE':
        return 'border-amber-200 hover:border-amber-300 bg-amber-50/20';
      default:
        return 'border-slate-200 bg-white';
    }
  };

  const getActionLabel = () => {
    if (certificate.status === 'AUSENTE') return 'Emitir certidão';
    if (certificate.status === 'VENCIDA') return 'Emitir nova certidão';
    return 'Acessar portal oficial';
  };

  const getActionButtonStyle = () => {
    if (certificate.status === 'AUSENTE' || certificate.status === 'VENCIDA') {
      return 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm';
    }
    return 'bg-slate-100 hover:bg-slate-200 text-slate-700';
  };

  return (
    <div className={`rounded-xl border shadow-sm transition-all duration-150 p-5 ${getCardBorder()}`}>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left info */}
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {certificate.type}
            </span>
            <StatusBadge status={certificate.status} />
            {certificate.is_manually_overridden && (
              <span className="text-[11px] bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-full font-medium">
                Editado Manualmente
              </span>
            )}
          </div>

          <h4 className="text-base font-bold text-slate-900 leading-snug">
            {certificate.name}
          </h4>

          <p className="text-xs text-slate-500 font-medium">
            Emissor: {certificate.issuer}
          </p>

          <p className="text-xs text-slate-700 mt-1">
            {certificate.message}
          </p>
        </div>

        {/* Middle meta badge tags */}
        <div className="flex flex-wrap lg:flex-col items-start lg:items-end gap-2 shrink-0 text-xs">
          {certificate.expiration_date && (
            <div className="flex items-center text-slate-700 bg-slate-100/90 px-2.5 py-1 rounded-lg border border-slate-200 font-medium">
              <Calendar className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
              <span>Validade: <strong>{certificate.expiration_date}</strong></span>
            </div>
          )}

          {certificate.pages.length > 0 && (
            <div className="flex items-center text-slate-700 bg-slate-100/90 px-2.5 py-1 rounded-lg border border-slate-200 font-medium">
              <Layers className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
              <span>Páginas: <strong>{certificate.pages.join(', ')}</strong></span>
            </div>
          )}

          {certificate.cnpj_formatted && (
            <div className="text-[11px] text-slate-500 font-mono">
              CNPJ: {certificate.cnpj_formatted}
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="flex items-center space-x-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100">
          <a
            href={certificate.issuance_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${getActionButtonStyle()}`}
            title="Abrir página oficial de emissão"
          >
            <span>{getActionLabel()}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          {/* Details toggle */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            title="Ver detalhes da análise"
          >
            {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expandable details & manual override */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-600 space-y-3 bg-slate-50/70 p-3.5 rounded-lg">
          {certificate.snippet && (
            <div>
              <span className="font-semibold text-slate-700 block mb-0.5">
                Trecho identificado no processo:
              </span>
              <p className="font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-800 break-words">
                "{certificate.snippet}"
              </p>
            </div>
          )}

          {certificate.validity_rule_text && (
            <p className="text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
              ℹ️ {certificate.validity_rule_text}
            </p>
          )}

          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200">
            <span className="text-[11px] text-slate-400">
              Score de confiança da detecção: {certificate.confidence_score}%
            </span>

            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-700">Conferência manual:</span>
              <button
                disabled={isUpdating}
                onClick={() => onOverride('OK', true, 'Aprovado manualmente')}
                className="px-2.5 py-1 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 rounded font-semibold transition-colors"
              >
                Marcar como OK
              </button>
              <button
                disabled={isUpdating}
                onClick={() => onOverride('AUSENTE', false, 'Marcado como ausente')}
                className="px-2.5 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded font-semibold transition-colors"
              >
                Marcar como Ausente
              </button>
              <button
                disabled={isUpdating}
                onClick={() => onOverride('REVISAR_MANUALMENTE', true, 'Necessita revisão')}
                className="px-2.5 py-1 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded font-semibold transition-colors"
              >
                Marcar para Revisão
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
