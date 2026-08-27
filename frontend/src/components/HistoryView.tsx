import React from 'react';
import { 
  History, 
  FileText, 
  Trash2, 
  ChevronRight, 
  Building, 
  Clock, 
  Layers 
} from 'lucide-react';
import { ProcessSummary } from '../types';

interface HistoryViewProps {
  items: ProcessSummary[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
  isLoading: boolean;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  items,
  onSelect,
  onDelete,
  onClose,
  isLoading,
}) => {
  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-slate-100 text-slate-700 rounded-xl">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              Histórico de Processos Analisados
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Metadados salvos localmente em banco de dados SQLite
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition-colors"
        >
          Voltar para Análise
        </button>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-slate-400 text-sm">
          Carregando histórico...
        </div>
      ) : items.length === 0 ? (
        <div className="py-12 text-center text-slate-400 text-sm">
          <History className="w-10 h-10 mx-auto text-slate-300 mb-2" />
          Nenhum processo analisado anteriormente.
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {items.map((item) => (
            <div
              key={item.id}
              className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/80 px-3 rounded-xl transition-colors group cursor-pointer"
              onClick={() => onSelect(item.id)}
            >
              <div className="flex items-start space-x-3 min-w-0">
                <div className="p-2 bg-primary-50 text-primary-600 rounded-lg shrink-0 mt-0.5">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="truncate">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-bold text-slate-900 truncate">
                      {item.filename}
                    </h4>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border ${
                        item.overall_status === 'REGULAR'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {item.overall_status === 'REGULAR' ? 'Sem Pendências' : `${item.total_pending} Pendência(s)`}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-xs text-slate-500 font-medium">
                    {item.supplier_name && (
                      <span className="flex items-center">
                        <Building className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        {item.supplier_name}
                      </span>
                    )}
                    {item.cnpj && (
                      <span className="font-mono text-slate-600">
                        CNPJ: {item.cnpj}
                      </span>
                    )}
                    <span className="flex items-center">
                      <Layers className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {item.total_pages} páginas
                    </span>
                    <span className="flex items-center text-slate-400">
                      <Clock className="w-3.5 h-3.5 mr-1 text-slate-400" />
                      {formatDate(item.created_at)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(item.id);
                  }}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Excluir do histórico"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <div className="p-1 text-slate-400 group-hover:text-primary-600 group-hover:translate-x-0.5 transition-all">
                  <ChevronRight className="w-5 h-5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
