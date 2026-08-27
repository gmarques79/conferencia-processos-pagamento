import React from 'react';
import { ShieldCheck, PlusCircle } from 'lucide-react';

interface HeaderProps {
  onNewAnalysis: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNewAnalysis }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={onNewAnalysis}>
            <div className="p-2 bg-primary-600 rounded-lg text-white shadow-md">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 leading-tight">
                Conferência de Processos de Pagamento
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                Análise e Checklist de Certidões e Documentos
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onNewAnalysis}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-all hover:shadow"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Nova Análise</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
