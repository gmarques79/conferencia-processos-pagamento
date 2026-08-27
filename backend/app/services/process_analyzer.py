import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.config.supplier_rules import get_supplier_rule
from app.models.process_db import ProcessRecord
from app.schemas.supplier import SupplierInfo, SupplierRuleResult
from app.schemas.process import (
    ProcessAnalysisResponse,
    ProcessMetadata,
    FinalInstructions,
)
from app.schemas.certificate import CertificateStatus
from app.services.pdf_extractor import pdf_extractor
from app.services.cnpj_service import (
    normalize_cnpj,
    format_cnpj,
    extract_cnpj_candidates,
    validate_cnpj,
)
from app.services.certificate_classifier import evaluate_all_certificates
from app.services.additional_docs_service import evaluate_additional_documents
from app.services.instruction_service import generate_final_instructions

class ProcessAnalyzer:
    def analyze(
        self,
        pdf_path: Path | str,
        original_filename: str,
        file_size: int,
        db: Session | None = None,
        process_id: str | None = None,
        manual_cnpj: str | None = None,
        manual_supplier_name: str | None = None,
    ) -> ProcessAnalysisResponse:
        pid = process_id or str(uuid.uuid4())
        
        # 1. Extract text from PDF pages
        extracted = pdf_extractor.extract(pdf_path)
        pages_text = extracted.pages_text
        total_pages = extracted.total_pages

        # 2. CNPJ & Supplier identification
        candidates = extract_cnpj_candidates(pages_text)
        
        confirmed_cnpj: str | None = None
        corporate_name: str | None = None
        confidence = 0.0
        is_confirmed = False
        needs_confirmation = False

        if manual_cnpj and validate_cnpj(manual_cnpj):
            confirmed_cnpj = normalize_cnpj(manual_cnpj)
            corporate_name = manual_supplier_name
            confidence = 100.0
            is_confirmed = True
            needs_confirmation = False
        elif candidates:
            top = candidates[0]
            confirmed_cnpj = top.cnpj
            corporate_name = top.corporate_name
            confidence = top.confidence
            
            if len(candidates) > 1 and candidates[1].confidence > 40.0:
                needs_confirmation = True
                is_confirmed = False
            elif top.confidence >= 65.0:
                is_confirmed = True
                needs_confirmation = False
            else:
                needs_confirmation = True
                is_confirmed = False

        supplier_info = SupplierInfo(
            cnpj=confirmed_cnpj,
            cnpj_formatted=format_cnpj(confirmed_cnpj) if confirmed_cnpj else None,
            corporate_name=corporate_name,
            confidence=confidence,
            is_confirmed=is_confirmed,
            needs_confirmation=needs_confirmation,
            candidates=candidates,
        )

        # 3. Apply Supplier Rules
        rule = get_supplier_rule(confirmed_cnpj)
        supplier_rule_res = SupplierRuleResult(
            cnpj=rule.cnpj,
            display_name=corporate_name or rule.display_name,
            report_required=rule.report_required,
            report_name=rule.report_name,
            instructions=rule.instructions,
            warnings=rule.warnings,
        )

        # 4. Evaluate Certificates
        certificates = evaluate_all_certificates(
            pages_text=pages_text,
            confirmed_supplier_cnpj=confirmed_cnpj,
        )

        # 5. Evaluate Additional Documents
        additional_docs = evaluate_additional_documents(
            pages_text=pages_text,
            supplier_rule=supplier_rule_res,
        )

        # 6. Generate Dynamic Final Instructions
        final_instructions = generate_final_instructions(
            supplier=supplier_info,
            supplier_rule=supplier_rule_res,
            certificates=certificates,
            additional_docs=additional_docs,
        )

        # Count total pending items
        total_pending = len(final_instructions.pending_items)

        # 7. Collect Warnings
        all_warnings: list[str] = list(extracted.warnings)
        if needs_confirmation and len(candidates) > 1:
            all_warnings.append(
                "Encontramos mais de um CNPJ possível no processo. Confirme ou selecione o fornecedor correto."
            )
        elif not confirmed_cnpj:
            all_warnings.append(
                "Não foi possível identificar automaticamente o fornecedor. Insira o CNPJ manualmente."
            )
        if supplier_rule_res.warnings:
            all_warnings.extend(supplier_rule_res.warnings)

        metadata = ProcessMetadata(
            id=pid,
            filename=original_filename,
            created_at=datetime.now(timezone.utc),
            total_pages=total_pages,
            file_size_bytes=file_size,
            scanned_pages_count=len(extracted.scanned_pages),
            is_ocr_used=extracted.is_ocr_used,
            ocr_available=extracted.ocr_available,
        )

        response = ProcessAnalysisResponse(
            id=pid,
            metadata=metadata,
            supplier=supplier_info,
            certificates=certificates,
            additional_documents=additional_docs,
            supplier_rules=supplier_rule_res,
            final_instructions=final_instructions,
            warnings=all_warnings,
            total_pending=total_pending,
        )

        # 8. Persist to Database if session provided
        if db:
            record = ProcessRecord(
                id=pid,
                filename=original_filename,
                created_at=metadata.created_at,
                total_pages=total_pages,
                cnpj=confirmed_cnpj,
                supplier_name=supplier_rule_res.display_name,
                total_pending=total_pending,
                overall_status=final_instructions.overall_status,
                analysis_json=json.dumps(response.model_dump(mode="json")),
            )
            # Merge or add
            db.merge(record)
            db.commit()

        return response

process_analyzer = ProcessAnalyzer()
