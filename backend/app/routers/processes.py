import os
import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config.settings import settings
from app.models.process_db import ProcessRecord
from app.schemas.process import (
    ProcessAnalysisResponse,
    ProcessSummary,
    UpdateSupplierRequest,
    UpdateCertificateOverrideRequest,
    UpdateDocOverrideRequest,
)
from app.schemas.certificate import CertificateStatus
from app.schemas.document import DocumentStatus
from app.config.supplier_rules import get_supplier_rule
from app.schemas.supplier import SupplierRuleResult
from app.services.cnpj_service import validate_cnpj, normalize_cnpj, format_cnpj
from app.services.instruction_service import generate_final_instructions
from app.services.process_analyzer import process_analyzer

router = APIRouter(prefix="/processes", tags=["processes"])

@router.post("/analyze", response_model=ProcessAnalysisResponse)
async def analyze_process(
    file: UploadFile = File(...),
    manual_cnpj: str | None = Form(None),
    manual_supplier_name: str | None = Form(None),
    db: Session = Depends(get_db),
):
    # Validate extension
    filename = file.filename or "processo.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado não parece ser um PDF válido. Apenas arquivos .pdf são aceitos.",
        )

    # Validate content type if provided
    if file.content_type and file.content_type != "application/pdf":
        # Some browsers might send application/octet-stream or application/x-pdf
        if "pdf" not in file.content_type.lower() and file.content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de arquivo inválido. Por favor, envie um documento PDF.",
            )

    # Generate secure random temp file
    temp_filename = f"proc_{uuid.uuid4().hex}.pdf"
    temp_path = settings.TEMP_DIR / temp_filename
    
    file_size = 0
    try:
        with open(temp_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"O arquivo excede o limite máximo permitido de {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.",
                    )
                f.write(chunk)

        # Execute analysis
        response = process_analyzer.analyze(
            pdf_path=temp_path,
            original_filename=filename,
            file_size=file_size,
            db=db,
            manual_cnpj=manual_cnpj,
            manual_supplier_name=manual_supplier_name,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível ler este PDF: {str(e)}",
        )
    finally:
        # Secure cleanup of temporary file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

@router.get("", response_model=list[ProcessSummary])
def list_processes(db: Session = Depends(get_db)):
    records = db.query(ProcessRecord).order_by(ProcessRecord.created_at.desc()).limit(100).all()
    return [
        ProcessSummary(
            id=r.id,
            filename=r.filename,
            created_at=r.created_at,
            cnpj=r.cnpj,
            supplier_name=r.supplier_name,
            total_pending=r.total_pending,
            overall_status=r.overall_status,
            total_pages=r.total_pages,
        )
        for r in records
    ]

@router.get("/{process_id}", response_model=ProcessAnalysisResponse)
def get_process(process_id: str, db: Session = Depends(get_db)):
    record = db.query(ProcessRecord).filter(ProcessRecord.id == process_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado no histórico.")
    return ProcessAnalysisResponse(**record.get_analysis_data())

@router.post("/{process_id}/supplier", response_model=ProcessAnalysisResponse)
def update_supplier(
    process_id: str,
    payload: UpdateSupplierRequest,
    db: Session = Depends(get_db),
):
    record = db.query(ProcessRecord).filter(ProcessRecord.id == process_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    data = record.get_analysis_data()
    resp_obj = ProcessAnalysisResponse(**data)

    clean_cnpj = normalize_cnpj(payload.cnpj)
    if not validate_cnpj(clean_cnpj):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ informado inválido.")

    # Update supplier info
    resp_obj.supplier.cnpj = clean_cnpj
    resp_obj.supplier.cnpj_formatted = format_cnpj(clean_cnpj)
    if payload.corporate_name:
        resp_obj.supplier.corporate_name = payload.corporate_name
    resp_obj.supplier.is_confirmed = True
    resp_obj.supplier.needs_confirmation = False

    # Re-evaluate supplier rules
    rule = get_supplier_rule(clean_cnpj)
    resp_obj.supplier_rules = SupplierRuleResult(
        cnpj=rule.cnpj,
        display_name=payload.corporate_name or rule.display_name,
        report_required=rule.report_required,
        report_name=rule.report_name,
        instructions=rule.instructions,
        warnings=rule.warnings,
    )

    # Re-check certificate divergence
    for cert in resp_obj.certificates:
        if cert.found and cert.cnpj and not cert.is_manually_overridden:
            if cert.cnpj != clean_cnpj:
                cert.status = CertificateStatus.CNPJ_DIVERGENTE
                cert.message = f"CNPJ da certidão ({cert.cnpj_formatted}) não corresponde ao fornecedor ({resp_obj.supplier.cnpj_formatted})."
            elif cert.status == CertificateStatus.CNPJ_DIVERGENTE:
                # Restored to valid or expired
                cert.status = CertificateStatus.OK
                cert.message = f"Certidão regular e correspondente ao fornecedor. Válida até {cert.expiration_date}."

    # Update dynamic instructions
    resp_obj.final_instructions = generate_final_instructions(
        supplier=resp_obj.supplier,
        supplier_rule=resp_obj.supplier_rules,
        certificates=resp_obj.certificates,
        additional_docs=resp_obj.additional_documents,
    )
    resp_obj.total_pending = len(resp_obj.final_instructions.pending_items)

    # Update DB
    record.cnpj = clean_cnpj
    record.supplier_name = resp_obj.supplier_rules.display_name
    record.total_pending = resp_obj.total_pending
    record.overall_status = resp_obj.final_instructions.overall_status
    record.analysis_json = json.dumps(resp_obj.model_dump(mode="json"))
    db.commit()

    return resp_obj

@router.post("/{process_id}/override-certificate", response_model=ProcessAnalysisResponse)
def override_certificate(
    process_id: str,
    payload: UpdateCertificateOverrideRequest,
    db: Session = Depends(get_db),
):
    record = db.query(ProcessRecord).filter(ProcessRecord.id == process_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    data = record.get_analysis_data()
    resp_obj = ProcessAnalysisResponse(**data)

    for cert in resp_obj.certificates:
        if cert.type == payload.cert_type:
            cert.status = payload.status
            cert.found = payload.found
            cert.is_manually_overridden = True
            cert.manual_notes = payload.manual_notes
            if payload.status == CertificateStatus.OK:
                cert.message = "Marcada manualmente como regular pelo usuário."
            elif payload.status == CertificateStatus.AUSENTE:
                cert.message = "Marcada manualmente como pendente/ausente pelo usuário."

    # Update instructions
    resp_obj.final_instructions = generate_final_instructions(
        supplier=resp_obj.supplier,
        supplier_rule=resp_obj.supplier_rules,
        certificates=resp_obj.certificates,
        additional_docs=resp_obj.additional_documents,
    )
    resp_obj.total_pending = len(resp_obj.final_instructions.pending_items)

    record.total_pending = resp_obj.total_pending
    record.overall_status = resp_obj.final_instructions.overall_status
    record.analysis_json = json.dumps(resp_obj.model_dump(mode="json"))
    db.commit()

    return resp_obj

@router.post("/{process_id}/override-document", response_model=ProcessAnalysisResponse)
def override_document(
    process_id: str,
    payload: UpdateDocOverrideRequest,
    db: Session = Depends(get_db),
):
    record = db.query(ProcessRecord).filter(ProcessRecord.id == process_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")

    data = record.get_analysis_data()
    resp_obj = ProcessAnalysisResponse(**data)

    for doc in resp_obj.additional_documents:
        if doc.type == payload.doc_type:
            doc.status = payload.status
            doc.found = payload.found
            doc.is_manually_overridden = True
            if payload.status == DocumentStatus.OK:
                doc.message = "Marcado manualmente como presente pelo usuário."
            elif payload.status == DocumentStatus.AUSENTE:
                doc.message = "Marcado manualmente como ausente pelo usuário."

    resp_obj.final_instructions = generate_final_instructions(
        supplier=resp_obj.supplier,
        supplier_rule=resp_obj.supplier_rules,
        certificates=resp_obj.certificates,
        additional_docs=resp_obj.additional_documents,
    )
    resp_obj.total_pending = len(resp_obj.final_instructions.pending_items)

    record.total_pending = resp_obj.total_pending
    record.overall_status = resp_obj.final_instructions.overall_status
    record.analysis_json = json.dumps(resp_obj.model_dump(mode="json"))
    db.commit()

    return resp_obj

@router.delete("/{process_id}")
def delete_process(process_id: str, db: Session = Depends(get_db)):
    record = db.query(ProcessRecord).filter(ProcessRecord.id == process_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado.")
    db.delete(record)
    db.commit()
    return {"message": "Processo removido com sucesso."}
