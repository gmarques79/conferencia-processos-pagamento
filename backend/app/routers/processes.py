import os
import uuid
import tempfile
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.config.settings import settings
from app.schemas.process import ProcessAnalysisResponse, RecalculateRequest
from app.schemas.certificate import CertificateStatus
from app.schemas.supplier import SupplierRuleResult
from app.config.supplier_rules import get_supplier_rule
from app.services.cnpj_service import validate_cnpj, normalize_cnpj, format_cnpj
from app.services.instruction_service import generate_final_instructions
from app.services.process_analyzer import process_analyzer

logger = logging.getLogger("processes_router")
router = APIRouter(prefix="/processes", tags=["processes"])

@router.post("/analyze", response_model=ProcessAnalysisResponse)
async def analyze_process(
    file: UploadFile = File(...),
    manual_cnpj: str | None = Form(None),
    manual_supplier_name: str | None = Form(None),
):
    """
    Stateless process analysis endpoint:
    Receives PDF, extracts text, identifies certificates and supplier rules,
    and returns complete checklist and instructions. No data is persisted.
    """
    filename = file.filename or "processo.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado não parece ser um PDF válido. Apenas arquivos .pdf são aceitos.",
        )

    # Validate content type if provided
    if file.content_type and file.content_type != "application/pdf":
        if "pdf" not in file.content_type.lower() and file.content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de arquivo inválido. Por favor, envie um documento PDF.",
            )

    # Create temporary file safely
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        prefix="proc_",
        dir=settings.TEMP_DIR,
        delete=False,
    )
    temp_path = Path(temp_file.name)
    
    file_size = 0
    first_chunk = True
    try:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            if first_chunk:
                first_chunk = False
                # Validate PDF magic header (%PDF-)
                if not chunk.startswith(b"%PDF-"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="O conteúdo do arquivo não corresponde a um documento PDF válido.",
                    )
            
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"O arquivo excede o limite máximo permitido de {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.",
                )
            temp_file.write(chunk)
        
        temp_file.flush()
        temp_file.close()

        # Run stateless analysis
        response = process_analyzer.analyze(
            pdf_path=temp_path,
            original_filename=filename,
            file_size=file_size,
            manual_cnpj=manual_cnpj,
            manual_supplier_name=manual_supplier_name,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no processamento do PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Não foi possível processar este PDF: {str(e)}",
        )
    finally:
        if not temp_file.closed:
            temp_file.close()
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as ex:
                logger.warning(f"Não foi possível excluir arquivo temporário {temp_path}: {ex}")

@router.post("/recalculate", response_model=ProcessAnalysisResponse)
def recalculate_analysis(payload: RecalculateRequest):
    """
    Stateless endpoint to recalculate rules and dynamic instructions
    when user manually changes CNPJ or updates status.
    """
    resp_obj = payload.analysis

    if payload.new_supplier_cnpj:
        clean_cnpj = normalize_cnpj(payload.new_supplier_cnpj)
        if not validate_cnpj(clean_cnpj):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ informado inválido.")

        resp_obj.supplier.cnpj = clean_cnpj
        resp_obj.supplier.cnpj_formatted = format_cnpj(clean_cnpj)
        if payload.new_supplier_name:
            resp_obj.supplier.corporate_name = payload.new_supplier_name
        resp_obj.supplier.is_confirmed = True
        resp_obj.supplier.needs_confirmation = False

        # Re-evaluate supplier rules
        rule = get_supplier_rule(clean_cnpj)
        resp_obj.supplier_rules = SupplierRuleResult(
            cnpj=rule.cnpj,
            display_name=payload.new_supplier_name or rule.display_name,
            report_required=rule.report_required,
            report_name=rule.report_name,
            instructions=rule.instructions,
            warnings=rule.warnings,
        )

        # Re-evaluate certificate divergence
        for cert in resp_obj.certificates:
            if cert.found and cert.cnpj and not cert.is_manually_overridden:
                if cert.cnpj != clean_cnpj:
                    cert.status = CertificateStatus.CNPJ_DIVERGENTE
                    cert.message = f"CNPJ da certidão ({cert.cnpj_formatted}) não corresponde ao fornecedor ({resp_obj.supplier.cnpj_formatted})."
                elif cert.status == CertificateStatus.CNPJ_DIVERGENTE:
                    cert.status = CertificateStatus.OK
                    cert.message = f"Certidão regular e correspondente ao fornecedor. Válida até {cert.expiration_date}."

    # Recalculate dynamic instructions
    resp_obj.final_instructions = generate_final_instructions(
        supplier=resp_obj.supplier,
        supplier_rule=resp_obj.supplier_rules,
        certificates=resp_obj.certificates,
        additional_docs=resp_obj.additional_documents,
    )
    resp_obj.total_pending = len(resp_obj.final_instructions.pending_items)

    return resp_obj
