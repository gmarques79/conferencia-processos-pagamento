import React, { useState, useRef } from 'react';
import { Upload, FileText, X, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
  error: string | null;
}

const ANALYSIS_STEPS = [
  'Lendo PDF e extraindo texto...',
  'Identificando fornecedor e CNPJ...',
  'Verificando as 5 certidões obrigatórias...',
  'Aplicando regras específicas do fornecedor...',
  'Gerando checklist e instruções finais...',
];

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  isLoading,
  error,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cycle through step messages while loading
  React.useEffect(() => {
    let interval: any;
    if (isLoading) {
      setCurrentStepIndex(0);
      interval = setInterval(() => {
        setCurrentStepIndex((prev) => (prev + 1) % ANALYSIS_STEPS.length);
      }, 1200);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setValidationError('Apenas arquivos no formato PDF são permitidos.');
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setValidationError('O arquivo excede o limite máximo permitido de 50 MB.');
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto py-8 px-4">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Conferência de Processos de Pagamento
        </h2>
        <p className="mt-3 text-base text-slate-600 max-w-xl mx-auto">
          Envie o processo em PDF para verificar certidões e documentos necessários.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
        {!selectedFile ? (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
              dragActive
                ? 'border-primary-500 bg-primary-50/50 scale-[1.01]'
                : 'border-slate-300 hover:border-primary-400 hover:bg-slate-50/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleChange}
              className="hidden"
            />
            <div className="w-16 h-16 mx-auto mb-4 bg-primary-50 text-primary-600 rounded-full flex items-center justify-center">
              <Upload className="w-8 h-8" />
            </div>
            <p className="text-base font-semibold text-slate-800">
              Arraste e solte o PDF do processo aqui
            </p>
            <p className="text-sm text-slate-500 mt-1">
              ou clique para selecionar do seu computador
            </p>
            <span className="inline-block mt-4 text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
              Aceita somente arquivos .PDF (até 50 MB)
            </span>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center space-x-3 overflow-hidden">
                <div className="p-2.5 bg-red-100 text-red-600 rounded-lg shrink-0">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="truncate">
                  <p className="text-sm font-semibold text-slate-900 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              {!isLoading && (
                <button
                  onClick={() => setSelectedFile(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                  title="Remover arquivo"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {isLoading ? (
              <div className="p-6 bg-primary-50 rounded-xl border border-primary-100 text-center space-y-4">
                <div className="flex items-center justify-center space-x-3 text-primary-700">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span className="font-semibold text-base">
                    Analisando processo...
                  </span>
                </div>
                <p className="text-sm text-primary-800 font-medium animate-pulse">
                  {ANALYSIS_STEPS[currentStepIndex]}
                </p>
                <div className="w-full bg-primary-200/60 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-primary-600 h-1.5 rounded-full w-full animate-indeterminate" />
                </div>
              </div>
            ) : (
              <button
                onClick={handleSubmit}
                className="w-full py-3.5 px-6 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl shadow-md transition-all flex items-center justify-center space-x-2 text-base hover:shadow-lg active:scale-[0.99]"
              >
                <span>Analisar Processo</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {(validationError || error) && (
          <div className="mt-4 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-3 text-red-700 text-sm">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Erro na análise</p>
              <p className="text-xs text-red-600 mt-0.5">{validationError || error}</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-500 text-center">
        <div className="p-3 bg-white/70 border border-slate-200 rounded-lg">
          🔒 <strong className="text-slate-700">100% Local:</strong> Seus documentos não saem do seu computador.
        </div>
        <div className="p-3 bg-white/70 border border-slate-200 rounded-lg">
          ⚡ <strong className="text-slate-700">5 Certidões:</strong> Conferência automática de validade e CNPJ.
        </div>
        <div className="p-3 bg-white/70 border border-slate-200 rounded-lg">
          📋 <strong className="text-slate-700">Regras e Checklist:</strong> Orientações imediatas para finalização.
        </div>
      </div>
    </div>
  );
};
