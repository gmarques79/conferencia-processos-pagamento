from app.schemas.certificate import CertificateResult, CertificateStatus
from app.schemas.document import AdditionalDocumentResult, AdditionalDocType, DocumentStatus
from app.schemas.supplier import SupplierInfo, SupplierRuleResult
from app.schemas.process import FinalInstructions

def generate_final_instructions(
    supplier: SupplierInfo,
    supplier_rule: SupplierRuleResult,
    certificates: list[CertificateResult],
    additional_docs: list[AdditionalDocumentResult],
) -> FinalInstructions:
    """
    Generates dynamic final instructions and checklist of pending actions.
    """
    pending_items: list[str] = []
    completed_items: list[str] = []

    supplier_display = supplier.corporate_name or supplier_rule.display_name or "Fornecedor não identificado"
    cnpj_display = supplier.cnpj_formatted or supplier.cnpj or "Não identificado"

    # 1. Evaluate Certificates
    for cert in certificates:
        if cert.status == CertificateStatus.AUSENTE:
            pending_items.append(f"Emitir {cert.name}.")
        elif cert.status == CertificateStatus.VENCIDA:
            pending_items.append(f"Emitir nova {cert.name} (vencida em {cert.expiration_date}).")
        elif cert.status == CertificateStatus.CNPJ_DIVERGENTE:
            pending_items.append(
                f"Regularizar divergência de CNPJ na {cert.short_name} (Certidão: {cert.cnpj_formatted} vs Processo: {cnpj_display})."
            )
        elif cert.status == CertificateStatus.VALIDADE_NAO_IDENTIFICADA:
            pending_items.append(f"Revisar manualmente a validade da {cert.short_name}.")
        elif cert.status == CertificateStatus.REVISAR_MANUALMENTE:
            pending_items.append(f"Revisar manualmente a situação da {cert.short_name} ({cert.message}).")
        elif cert.status == CertificateStatus.OK:
            completed_items.append(f"{cert.short_name} regular e válida até {cert.expiration_date}.")

    # 2. Evaluate Supplier Rule Report
    if supplier_rule.report_required:
        warn_text = f" ({supplier_rule.warnings[0]})" if supplier_rule.warnings else ""
        pending_items.append(f"Gerar {supplier_rule.report_name}: {supplier_rule.instructions}{warn_text}")
    else:
        completed_items.append("Relatório específico de fornecedor: não exigido.")

    # 3. Evaluate Additional Documents
    for doc in additional_docs:
        if doc.type == AdditionalDocType.SUPPLIER_REPORT:
            continue  # already handled above
        
        if doc.type == AdditionalDocType.PAYMENT_DATA_SHEET:
            if doc.status == DocumentStatus.OK:
                completed_items.append(f"{doc.name} presente (páginas: {', '.join(map(str, doc.pages))}).")
            else:
                pending_items.append("Adicionar folha de dados para pagamento.")
                
        elif doc.type == AdditionalDocType.ATESTO:
            if doc.status == DocumentStatus.OK:
                completed_items.append(f"{doc.name} presente (páginas: {', '.join(map(str, doc.pages))}).")
            else:
                pending_items.append("Adicionar atesto assinado pelo responsável.")

    # Completion message
    if not pending_items:
        completion_msg = "Nenhuma pendência automática identificada. Faça a conferência final antes de encaminhar o processo."
        overall_status = "REGULAR"
    else:
        completion_msg = f"Existem {len(pending_items)} item(ns) pendente(s) ou que necessitam de conferência manual para conclusão do processo."
        overall_status = "PENDENTE"

    return FinalInstructions(
        supplier_name=supplier_display,
        cnpj=cnpj_display,
        pending_items=pending_items,
        completed_items=completed_items,
        completion_message=completion_msg,
        overall_status=overall_status,
    )
