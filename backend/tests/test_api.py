import io
import pytest
from app.config.certificate_links import CertificateType
from app.schemas.certificate import CertificateStatus
from app.schemas.document import DocumentStatus

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "ocr_available" in data

def test_upload_invalid_extension(client):
    file_content = b"not a pdf content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    response = client.post("/api/processes/analyze", files=files)
    assert response.status_code == 400
    assert "Apenas arquivos .pdf são aceitos" in response.json()["detail"]

def test_full_process_analysis_and_persistence(client, make_pdf):
    # Create synthetic PDF for Prime Beneficios
    pdf_bytes = make_pdf([
        # Page 1: Cover with supplier info
        """
        ESTADO DE SERGIPE
        PROCESSO DE PAGAMENTO Nº 2026/001
        Fornecedor Contratado: PRIME BENEFICIOS LTDA
        CNPJ: 05.340.639/0001-30
        Nota Fiscal: 4567
        """,
        # Page 2: Federal CND
        """
        RECEITA FEDERAL DO BRASIL
        CERTIDÃO NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO
        CNPJ: 05.340.639/0001-30
        Emitida em: 01/06/2026
        Válida até: 28/11/2026
        Código de controle: A123-B456
        """,
        # Page 3: Folha de dados
        """
        DADOS BANCÁRIOS PARA PAGAMENTO
        Banco: Banco do Brasil (001)
        Agência: 1234
        Conta: 5678-9
        PIX: 05340639000130
        """,
        # Page 4: Atesto
        """
        TERMO DE ATESTO
        ATESTO para os devidos fins que os serviços foram prestados a contento.
        Data: 15/08/2026
        """,
    ])

    files = {"file": ("processo_prime.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/processes/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    # Check process metadata
    assert data["metadata"]["filename"] == "processo_prime.pdf"
    assert data["metadata"]["total_pages"] == 4
    
    # Check supplier
    assert data["supplier"]["cnpj"] == "05340639000130"
    assert data["supplier"]["cnpj_formatted"] == "05.340.639/0001-30"

    # Check Prime Beneficios rule triggered
    assert data["supplier_rules"]["report_required"] is True
    assert data["supplier_rules"]["report_name"] == "Consumo Subunidade/Veículo"

    # Check certificates
    certs = data["certificates"]
    assert len(certs) == 5
    fed = next(c for c in certs if c["type"] == CertificateType.FEDERAL)
    assert fed["status"] == CertificateStatus.OK
    assert fed["found"] is True

    # FGTS, CNDT, ICMS, State CND should be AUSENTE
    fgts = next(c for c in certs if c["type"] == CertificateType.FGTS)
    assert fgts["status"] == CertificateStatus.AUSENTE
    assert fgts["found"] is False

    # Check history listing
    list_resp = client.get("/api/processes")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert items[0]["id"] == data["id"]
    assert items[0]["cnpj"] == "05340639000130"

    # Check process retrieval by ID
    get_resp = client.get(f"/api/processes/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]

def test_update_supplier_recalculates_rules(client, make_pdf):
    # Initially analyzed as Prime Beneficios
    pdf_bytes = make_pdf(["Fornecedor: 05.340.639/0001-30"])
    files = {"file": ("teste.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/processes/analyze", files=files)
    proc_id = res.json()["id"]

    # Now update supplier to Bamex Manutenções (28.008.410/0001-06)
    update_res = client.post(
        f"/api/processes/{proc_id}/supplier",
        json={"cnpj": "28.008.410/0001-06", "corporate_name": "Bamex Manutenções"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["supplier"]["cnpj"] == "28008410000106"
    assert updated_data["supplier_rules"]["report_required"] is True
    assert updated_data["supplier_rules"]["report_name"] == "Manutenções"
    assert any("Finalizada (Somente)" in w for w in updated_data["supplier_rules"]["warnings"])

def test_override_certificate_and_document(client, make_pdf):
    pdf_bytes = make_pdf(["Processo simples"])
    files = {"file": ("teste2.pdf", pdf_bytes, "application/pdf")}
    res = client.post("/api/processes/analyze", files=files)
    proc_id = res.json()["id"]

    # Override FGTS as found / OK manually
    override_cert = client.post(
        f"/api/processes/{proc_id}/override-certificate",
        json={
            "cert_type": CertificateType.FGTS,
            "status": CertificateStatus.OK,
            "found": True,
            "manual_notes": "Conferido no processo físico",
        },
    )
    assert override_cert.status_code == 200
    cert_data = override_cert.json()
    fgts = next(c for c in cert_data["certificates"] if c["type"] == CertificateType.FGTS)
    assert fgts["status"] == CertificateStatus.OK
    assert fgts["is_manually_overridden"] is True

    # Override Folha de Dados as OK manually
    override_doc = client.post(
        f"/api/processes/{proc_id}/override-document",
        json={
            "doc_type": "PAYMENT_DATA_SHEET",
            "status": DocumentStatus.OK,
            "found": True,
        },
    )
    assert override_doc.status_code == 200
    doc_data = override_doc.json()
    pay = next(d for d in doc_data["additional_documents"] if d["type"] == "PAYMENT_DATA_SHEET")
    assert pay["status"] == DocumentStatus.OK
    assert pay["is_manually_overridden"] is True
