import React, { useState } from 'react';
import { 
  FileCheck, 
  CreditCard, 
  FileSpreadsheet, 
  AlertTriangle, 
  Layers, 
  ChevronDown, 
  ChevronUp 
} from 'lucide-react';
import { AdditionalDocumentResult, DocumentStatus, AdditionalDocType } from '../types';
import { StatusBadge } from './StatusBadge';

interface AdditionalDocsCardProps {
  documents: AdditionalDocumentResult[];
  onOverride: (docType: string, status: DocumentStatus, found: boolean) => Promise<void>;
  isUpdating: boolean;
}

export const AdditionalDocsCard: React.FC<AdditionalDocsCardProps> = ({
  documents,
  onOverride,
  isUpdating,
}) => {
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  const getDocIcon = (type: AdditionalDocType) => {
    switch (type) {
      case 'SUPPLIER_REPORT':
        return <FileSpreadsheet className="w-5 h-5 text-indigo-600" />;
      case 'PAYMENT_DATA_SHEET':
        return <CreditCard className="w-5 h-5 text-sky-600" />;
      case 'ATESTO':
        return <FileCheck className="w-5 h-5 text-emerald-600" />;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-6">
      <div className="border-b border-slate-100 pb-4 mb-4">
        <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
          <span>Documentos Complementares e Relatórios</span>
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Verificação de folha de dados bancários, atesto e relatórios específicos por fornecedor.
        </p>
      </div>

      <div className="space-y-3.5">
        {documents.map((doc) => {
          const isExpanded = expandedDoc === doc.type;
          return (
            <div
              key={doc.type}
              className={`rounded-xl border p-4 transition-all ${
                doc.status === 'OK'
                  ? 'border-emerald-200 bg-emerald-50/10'
                  : doc.status === 'NAO_APLICAVEL'
                  ? 'border-slate-200 bg-slate-50/50'
                  : doc.status === 'REVISAR_MANUALMENTE'
                  ? 'border-amber-200 bg-amber-50/20'
                  : 'border-red-200 bg-red-50/20'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-slate-100 rounded-lg shrink-0 mt-0.5">
                    {getDocIcon(doc.type)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-bold text-slate-900">
                        {doc.name}
                      </h4>
                      <StatusBadge status={doc.status} size="sm" />
                      {doc.is_manually_overridden && (
                        <span className="text-[10px] bg-purple-50 text-purple-700 border border-purple-200 px-1.5 py-0.2 rounded-full font-medium">
                          Manual
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 mt-1">
                      {doc.message}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  {doc.pages.length > 0 && (
                    <span className="text-xs text-slate-600 bg-slate-100 px-2 py-1 rounded font-medium flex items-center">
                      <Layers className="w-3 h-3 mr-1 text-slate-400" />
                      Páginas: {doc.pages.join(', ')}
                    </span>
                  )}
                  <button
                    onClick={() => setExpandedDoc(isExpanded ? null : doc.type)}
                    className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Warnings for this document */}
              {doc.warnings && doc.warnings.length > 0 && (
                <div className="mt-3 p-3 bg-amber-100/70 border border-amber-300 rounded-lg flex items-start space-x-2.5 text-amber-900 text-xs font-medium">
                  <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <strong className="block text-amber-950 font-bold">Aviso Obrigatório:</strong>
                    {doc.warnings.map((w, idx) => (
                      <p key={idx}>{w}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Expandable details & override actions */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-slate-200/80 text-xs text-slate-600 space-y-2.5">
                  {doc.instructions && (
                    <div>
                      <span className="font-semibold text-slate-700 block">Orientação:</span>
                      <p className="text-slate-600">{doc.instructions}</p>
                    </div>
                  )}

                  {doc.snippet && (
                    <div>
                      <span className="font-semibold text-slate-700 block">Trecho identificado:</span>
                      <p className="font-mono text-[11px] bg-white p-2 rounded border border-slate-200 text-slate-800 break-words mt-0.5">
                        "{doc.snippet}"
                      </p>
                    </div>
                  )}

                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-200">
                    <span className="text-xs font-semibold text-slate-700">Conferência manual:</span>
                    <button
                      disabled={isUpdating}
                      onClick={() => onOverride(doc.type, 'OK', true)}
                      className="px-2.5 py-1 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 rounded font-semibold transition-colors"
                    >
                      Marcar como Presente
                    </button>
                    <button
                      disabled={isUpdating}
                      onClick={() => onOverride(doc.type, 'AUSENTE', false)}
                      className="px-2.5 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded font-semibold transition-colors"
                    >
                      Marcar como Ausente
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
