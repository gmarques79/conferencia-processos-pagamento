import React from 'react';
import { 
  CheckCircle2, 
  AlertCircle, 
  ListChecks, 
  CheckCheck, 
  Info
} from 'lucide-react';
import { FinalInstructions } from '../types';

interface InstructionsSectionProps {
  instructions: FinalInstructions;
}

export const InstructionsSection: React.FC<InstructionsSectionProps> = ({
  instructions,
}) => {
  const hasPending = instructions.pending_items.length > 0;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 mb-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl ${hasPending ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
            <ListChecks className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 uppercase tracking-tight">
              Instruções para Finalizar o Processo
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Checklist gerado automaticamente com base na análise do fornecedor e certidões
            </p>
          </div>
        </div>

        <span
          className={`px-3 py-1 text-xs font-bold rounded-full border ${
            hasPending
              ? 'bg-amber-50 text-amber-800 border-amber-200'
              : 'bg-emerald-50 text-emerald-800 border-emerald-200'
          }`}
        >
          {hasPending ? `${instructions.pending_items.length} Pendência(s)` : 'Sem Pendências'}
        </span>
      </div>

      <div className="space-y-4">
        {hasPending ? (
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-red-600 mb-3 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1.5" />
              Ações Necessárias / Pendências a Resolver:
            </h4>
            <ul className="space-y-2.5">
              {instructions.pending_items.map((item, idx) => (
                <li
                  key={idx}
                  className="flex items-start space-x-3 p-3 bg-red-50/50 border border-red-100 rounded-xl text-sm font-medium text-slate-800"
                >
                  <span className="flex items-center justify-center w-5 h-5 rounded-full bg-red-600 text-white text-xs font-bold shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start space-x-3">
            <CheckCheck className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-emerald-900">
                Nenhuma pendência automática identificada!
              </h4>
              <p className="text-xs text-emerald-700 mt-1">
                Todas as 5 certidões obrigatórias, dados de pagamento e atesto foram identificados como válidos e regulares.
              </p>
            </div>
          </div>
        )}

        {instructions.completed_items.length > 0 && (
          <div className="pt-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center">
              <CheckCircle2 className="w-4 h-4 mr-1.5 text-emerald-600" />
              Itens Verificados com Sucesso:
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600">
              {instructions.completed_items.map((item, idx) => (
                <div key={idx} className="flex items-center space-x-2 bg-slate-50 p-2 rounded-lg border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="truncate">{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center space-x-2.5 text-xs text-slate-500">
          <Info className="w-4 h-4 text-slate-400 shrink-0" />
          <span>
            <strong>Atenção:</strong> Esta aplicação é uma ferramenta de apoio. Realize a conferência visual final dos documentos antes de tramitar o processo de pagamento.
          </span>
        </div>
      </div>
    </div>
  );
};
