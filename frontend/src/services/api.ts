import { 
  ProcessAnalysisResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export async function analyzeProcess(
  file: File,
  manualCnpj?: string,
  manualSupplierName?: string
): Promise<ProcessAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (manualCnpj) {
    formData.append('manual_cnpj', manualCnpj);
  }
  if (manualSupplierName) {
    formData.append('manual_supplier_name', manualSupplierName);
  }

  const response = await fetch(`${API_BASE_URL}/processes/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Erro ao processar o arquivo PDF.';
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function recalculateAnalysis(
  analysis: ProcessAnalysisResponse,
  newSupplierCnpj?: string,
  newSupplierName?: string
): Promise<ProcessAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/processes/recalculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis,
      new_supplier_cnpj: newSupplierCnpj,
      new_supplier_name: newSupplierName,
    }),
  });

  if (!response.ok) {
    let errorDetail = 'Erro ao recalcular regras do processo.';
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
