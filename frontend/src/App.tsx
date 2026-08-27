import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { SupplierCard } from './components/SupplierCard';
import { CertificateCard } from './components/CertificateCard';
import { AdditionalDocsCard } from './components/AdditionalDocsCard';
import { InstructionsSection } from './components/InstructionsSection';
import { WarningsBanner } from './components/WarningsBanner';
import { 
  ProcessAnalysisResponse, 
  CertificateStatus, 
  DocumentStatus 
} from './types';
import { 
  analyzeProcess, 
  recalculateAnalysis, 
} from './services/api';
import { ArrowLeft } from 'lucide-react';

export const App: React.FC = () => {
  const [currentResult, setCurrentResult] = useState<ProcessAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await analyzeProcess(file);
      setCurrentResult(response);
    } catch (err: any) {
      setError(err.message || 'Erro ao processar o arquivo PDF.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateSupplier = async (cnpj: string, name?: string) => {
    if (!currentResult) return;
    setIsUpdating(true);
    try {
      const updated = await recalculateAnalysis(currentResult, cnpj, name);
      setCurrentResult(updated);
    } catch (err: any) {
      throw err;
    } finally {
      setIsUpdating(false);
    }
  };

  const handleOverrideCert = async (
    certType: string,
    status: CertificateStatus,
    found: boolean,
    notes?: string
  ) => {
    if (!currentResult) return;
    setIsUpdating(true);
    try {
      // Clone current result and update cert
      const updatedCerts = currentResult.certificates.map((c) => {
        if (c.type === certType) {
          let msg = c.message;
          if (status === 'OK') msg = 'Marcada manualmente como regular pelo usuário.';
          if (status === 'AUSENTE') msg = 'Marcada manualmente como ausente pelo usuário.';
          if (status === 'REVISAR_MANUALMENTE') msg = 'Marcada manualmente para revisão pelo usuário.';
          return {
            ...c,
            status,
            found,
            is_manually_overridden: true,
            manual_notes: notes || null,
            message: msg,
          };
        }
        return c;
      });

      const updatedAnalysis: ProcessAnalysisResponse = {
        ...currentResult,
        certificates: updatedCerts,
      };

      // Recalculate instructions statelessly
      const recalculated = await recalculateAnalysis(updatedAnalysis);
      setCurrentResult(recalculated);
    } catch (err: any) {
      alert(err.message || 'Erro ao atualizar certidão.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleOverrideDoc = async (
    docType: string,
    status: DocumentStatus,
    found: boolean
  ) => {
    if (!currentResult) return;
    setIsUpdating(true);
    try {
      const updatedDocs = currentResult.additional_documents.map((d) => {
        if (d.type === docType) {
          let msg = d.message;
          if (status === 'OK') msg = 'Marcado manualmente como presente pelo usuário.';
          if (status === 'AUSENTE') msg = 'Marcado manualmente como ausente pelo usuário.';
          return {
            ...d,
            status,
            found,
            is_manually_overridden: true,
            message: msg,
          };
        }
        return d;
      });

      const updatedAnalysis: ProcessAnalysisResponse = {
        ...currentResult,
        additional_documents: updatedDocs,
      };

      const recalculated = await recalculateAnalysis(updatedAnalysis);
      setCurrentResult(recalculated);
    } catch (err: any) {
      alert(err.message || 'Erro ao atualizar documento.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleNewAnalysis = () => {
    setCurrentResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header onNewAnalysis={handleNewAnalysis} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!currentResult ? (
          <FileUpload
            onFileSelect={handleFileUpload}
            isLoading={isLoading}
            error={error}
          />
        ) : (
          <div className="space-y-6">
            {/* Top Bar for Results */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleNewAnalysis}
                  className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Analisar outro arquivo"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                  <h2 className="text-base font-bold text-slate-900 leading-tight">
                    {currentResult.metadata.filename}
                  </h2>
                  <p className="text-xs text-slate-500 font-medium">
                    {currentResult.metadata.total_pages} páginas • Processamento stateless
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={handleNewAnalysis}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                >
                  Nova Análise
                </button>
              </div>
            </div>

            {/* Warnings banner */}
            <WarningsBanner warnings={currentResult.warnings} />

            {/* Supplier Card */}
            <SupplierCard
              supplier={currentResult.supplier}
              onUpdateSupplier={handleUpdateSupplier}
              isUpdating={isUpdating}
            />

            {/* 5 Mandatory Certificates Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6">
              <div className="border-b border-slate-100 pb-4 mb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">
                      Certidões Obrigatórias
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      As 5 certidões de regularidade exigidas para o processo de pagamento.
                    </p>
                  </div>
                  <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                    5 certidões
                  </span>
                </div>
              </div>

              <div className="space-y-3.5">
                {currentResult.certificates.map((cert) => (
                  <CertificateCard
                    key={cert.type}
                    certificate={cert}
                    onOverride={(status, found, notes) =>
                      handleOverrideCert(cert.type, status, found, notes)
                    }
                    isUpdating={isUpdating}
                  />
                ))}
              </div>
            </div>

            {/* Additional Documents & Reports */}
            <AdditionalDocsCard
              documents={currentResult.additional_documents}
              onOverride={handleOverrideDoc}
              isUpdating={isUpdating}
            />

            {/* Dynamic Final Instructions Section */}
            <InstructionsSection
              instructions={currentResult.final_instructions}
            />
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4">
          <p className="font-medium text-slate-600">
            Conferência de Processos de Pagamento — Ferramenta de Apoio Administrativo
          </p>
          <p className="text-slate-400 mt-1">
            Aplicação Stateless • Nenhum dado é persistido ou enviado a serviços externos
          </p>
        </div>
      </footer>
    </div>
  );
};
