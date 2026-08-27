import { 
  ProcessAnalysisResponse, 
  ProcessSummary, 
  CertificateStatus, 
  DocumentStatus 
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

export async function listProcesses(): Promise<ProcessSummary[]> {
  const response = await fetch(`${API_BASE_URL}/processes`);
  if (!response.ok) {
    throw new Error('Erro ao carregar histórico de processos.');
  }
  return response.json();
}

export async function getProcess(id: string): Promise<ProcessAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/processes/${id}`);
  if (!response.ok) {
    throw new Error('Processo não encontrado.');
  }
  return response.json();
}

export async function updateProcessSupplier(
  id: string,
  cnpj: string,
  corporateName?: string
): Promise<ProcessAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/processes/${id}/supplier`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cnpj, corporate_name: corporateName }),
  });

  if (!response.ok) {
    const errJson = await response.json();
    throw new Error(errJson.detail || 'Erro ao atualizar fornecedor.');
  }

  return response.json();
}

export async function overrideCertificate(
  id: string,
  certType: string,
  status: CertificateStatus,
  found: boolean,
  manualNotes?: string
): Promise<ProcessAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/processes/${id}/override-certificate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cert_type: certType,
      status,
      found,
      manual_notes: manualNotes,
    }),
  });

  if (!response.ok) {
    const errJson = await response.json();
    throw new Error(errJson.detail || 'Erro ao atualizar certidão.');
  }

  return response.json();
}

export async function overrideDocument(
  id: string,
  docType: string,
  status: DocumentStatus,
  found: boolean
): Promise<ProcessAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/processes/${id}/override-document`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doc_type: docType,
      status,
      found,
    }),
  });

  if (!response.ok) {
    const errJson = await response.json();
    throw new Error(errJson.detail || 'Erro ao atualizar documento.');
  }

  return response.json();
}

export async function deleteProcess(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/processes/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Erro ao excluir processo do histórico.');
  }
}
