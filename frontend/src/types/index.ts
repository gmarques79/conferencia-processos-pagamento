export type CertificateStatus = 
  | 'OK' 
  | 'AUSENTE' 
  | 'VENCIDA' 
  | 'CNPJ_DIVERGENTE' 
  | 'VALIDADE_NAO_IDENTIFICADA' 
  | 'REVISAR_MANUALMENTE';

export type CertificateType = 
  | 'FEDERAL' 
  | 'FGTS' 
  | 'CNDT' 
  | 'ICMS_DECLARATION' 
  | 'STATE_CND';

export interface CertificateResult {
  type: CertificateType;
  name: string;
  short_name: string;
  issuer: string;
  status: CertificateStatus;
  found: boolean;
  cnpj: string | null;
  cnpj_formatted: string | null;
  corporate_name: string | null;
  issue_date: string | null;
  expiration_date: string | null;
  calculated_validity: boolean;
  validity_rule_text: string | null;
  pages: number[];
  snippet: string | null;
  message: string;
  issuance_url: string;
  confidence_score: number;
  is_manually_overridden: boolean;
  manual_notes: string | null;
}

export interface SupplierCandidate {
  cnpj: string;
  cnpj_formatted: string;
  corporate_name: string | null;
  confidence: number;
  occurrences: number;
  page_numbers: number[];
  context_snippet: string | null;
}

export interface SupplierInfo {
  cnpj: string | null;
  cnpj_formatted: string | null;
  corporate_name: string | null;
  confidence: number;
  is_confirmed: boolean;
  needs_confirmation: boolean;
  candidates: SupplierCandidate[];
}

export interface SupplierRuleResult {
  cnpj: string;
  display_name: string;
  report_required: boolean;
  report_name: string | null;
  instructions: string;
  warnings: string[];
}

export type DocumentStatus = 'OK' | 'AUSENTE' | 'REVISAR_MANUALMENTE' | 'NAO_APLICAVEL';

export type AdditionalDocType = 'PAYMENT_DATA_SHEET' | 'ATESTO' | 'SUPPLIER_REPORT';

export interface AdditionalDocumentResult {
  type: AdditionalDocType;
  name: string;
  found: boolean;
  status: DocumentStatus;
  pages: number[];
  snippet: string | null;
  message: string;
  is_required: boolean;
  instructions: string | null;
  warnings: string[];
  is_manually_overridden: boolean;
}

export interface ProcessMetadata {
  id: string;
  filename: string;
  created_at: string;
  total_pages: number;
  file_size_bytes: number;
  scanned_pages_count: number;
  is_ocr_used: boolean;
  ocr_available: boolean;
}

export interface FinalInstructions {
  supplier_name: string;
  cnpj: string | null;
  pending_items: string[];
  completed_items: string[];
  completion_message: string;
  overall_status: 'REGULAR' | 'PENDENTE';
}

export interface ProcessAnalysisResponse {
  id: string;
  metadata: ProcessMetadata;
  supplier: SupplierInfo;
  certificates: CertificateResult[];
  additional_documents: AdditionalDocumentResult[];
  supplier_rules: SupplierRuleResult;
  final_instructions: FinalInstructions;
  warnings: string[];
  total_pending: number;
}
