import React, { useState } from 'react';
import { 
  Building2, 
  Copy, 
  Check, 
  Edit3, 
  AlertCircle, 
  CheckCircle,
  HelpCircle 
} from 'lucide-react';
import { SupplierInfo, SupplierCandidate } from '../types';

interface SupplierCardProps {
  supplier: SupplierInfo;
  onUpdateSupplier: (cnpj: string, name?: string) => Promise<void>;
  isUpdating: boolean;
}

export const SupplierCard: React.FC<SupplierCardProps> = ({
  supplier,
  onUpdateSupplier,
  isUpdating,
}) => {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editCnpj, setEditCnpj] = useState(supplier.cnpj_formatted || '');
  const [editName, setEditName] = useState(supplier.corporate_name || '');
  const [formError, setFormError] = useState<string | null>(null);

  const handleCopy = () => {
    if (supplier.cnpj_formatted || supplier.cnpj) {
      navigator.clipboard.writeText(supplier.cnpj_formatted || supplier.cnpj || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    const clean = editCnpj.replace(/\D/g, '');
    if (clean.length !== 14) {
      setFormError('O CNPJ deve conter exatamente 14 dígitos numéricos.');
      return;
    }
    try {
      await onUpdateSupplier(clean, editName.trim() || undefined);
      setIsEditing(false);
    } catch (err: any) {
      setFormError(err.message || 'Erro ao salvar novo CNPJ.');
    }
  };

  const handleSelectCandidate = async (candidate: SupplierCandidate) => {
    try {
      await onUpdateSupplier(candidate.cnpj, candidate.corporate_name || undefined);
    } catch (err: any) {
      setFormError(err.message || 'Erro ao selecionar CNPJ.');
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="flex items-start space-x-3.5">
          <div className="p-3 bg-primary-50 text-primary-700 rounded-xl mt-0.5">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Fornecedor Identificado
              </span>
              {supplier.is_confirmed ? (
                <span className="inline-flex items-center text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  <CheckCircle className="w-3 h-3 mr-1 text-emerald-600" />
                  Confirmado
                </span>
              ) : supplier.needs_confirmation ? (
                <span className="inline-flex items-center text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  <HelpCircle className="w-3 h-3 mr-1 text-amber-600" />
                  Requer Confirmação
                </span>
              ) : null}
            </div>

            <h3 className="text-xl font-bold text-slate-900 mt-0.5">
              {supplier.corporate_name || 'Razão Social não extraída'}
            </h3>

            <div className="flex items-center space-x-2 mt-1">
              <span className="text-sm font-mono font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                CNPJ: {supplier.cnpj_formatted || 'Não identificado'}
              </span>
              {supplier.confidence > 0 && (
                <span className="text-xs text-slate-400">
                  (Confiança: {supplier.confidence}%)
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
          <button
            onClick={handleCopy}
            disabled={!supplier.cnpj}
            className={`inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
              copied
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
            title="Copiar CNPJ para área de transferência"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                <span>Copiado!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copiar CNPJ</span>
              </>
            )}
          </button>

          <button
            onClick={() => {
              setIsEditing(!isEditing);
              setEditCnpj(supplier.cnpj_formatted || '');
              setEditName(supplier.corporate_name || '');
            }}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors"
          >
            <Edit3 className="w-4 h-4" />
            <span>{isEditing ? 'Cancelar' : 'Alterar CNPJ'}</span>
          </button>
        </div>
      </div>

      {/* Multiple Candidates Selection Banner */}
      {supplier.candidates && supplier.candidates.length > 1 && !isEditing && (
        <div className="mt-4 p-4 bg-amber-50/70 border border-amber-200 rounded-xl">
          <div className="flex items-center space-x-2 text-amber-800 text-sm font-semibold mb-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Encontramos mais de um CNPJ no processo. Confirme o fornecedor correto:</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 mt-2">
            {supplier.candidates.map((cand) => (
              <button
                key={cand.cnpj}
                onClick={() => handleSelectCandidate(cand)}
                disabled={isUpdating}
                className={`p-2.5 text-left rounded-lg border text-xs transition-all ${
                  cand.cnpj === supplier.cnpj
                    ? 'border-primary-500 bg-primary-50/80 ring-1 ring-primary-500'
                    : 'border-slate-200 bg-white hover:border-primary-300 hover:bg-slate-50'
                }`}
              >
                <div className="font-mono font-bold text-slate-900">
                  {cand.cnpj_formatted}
                </div>
                {cand.corporate_name && (
                  <div className="text-slate-600 truncate mt-0.5">
                    {cand.corporate_name}
                  </div>
                )}
                <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
                  <span>Páginas: {cand.page_numbers.join(', ')}</span>
                  <span className="font-medium text-slate-500">{cand.confidence}% conf.</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Manual Edit Form */}
      {isEditing && (
        <form onSubmit={handleSave} className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
          <h4 className="text-sm font-bold text-slate-800">
            Definir Fornecedor Manualmente
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                CNPJ do Fornecedor (14 dígitos)
              </label>
              <input
                type="text"
                value={editCnpj}
                onChange={(e) => setEditCnpj(e.target.value)}
                placeholder="00.000.000/0000-00"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Razão Social (Opcional)
              </label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Nome da empresa"
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
          </div>

          {formError && (
            <p className="text-xs text-red-600 font-medium">{formError}</p>
          )}

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-3.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isUpdating}
              className="px-4 py-1.5 text-xs font-bold text-white bg-primary-600 hover:bg-primary-700 rounded-lg shadow-sm transition-colors"
            >
              {isUpdating ? 'Atualizando...' : 'Confirmar e Reavaliar'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
