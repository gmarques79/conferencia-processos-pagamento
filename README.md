# Conferência de Processos de Pagamento

Aplicação web completa, funcional e de execução 100% local desenvolvida para auxiliar na conferência e auditoria de processos administrativos de pagamento de fornecedores.

O sistema recebe o processo em PDF, extrai e classifica o texto página a página, identifica fornecedores e CNPJ, valida as cinco certidões obrigatórias, confere documentos complementares (folha de dados bancários e atesto), aplica regras específicas de relatórios por fornecedor e apresenta um checklist claro com links oficiais diretos para emissão de certidões ausentes ou vencidas.

---

## 🔒 Privacidade e Segurança dos Dados

* **Execução 100% Local:** A análise do processo ocorre inteiramente no seu computador.
* **Sem envio para APIs externas:** Não utiliza Gemini, OpenAI ou qualquer serviço de terceiros em nuvem.
* **Limpeza de arquivos temporários:** Os arquivos PDF enviados são excluídos do disco imediatamente após a análise.
* **Persistência de metadados:** O banco de dados SQLite local armazena apenas metadados e resultados estruturados para histórico, nunca o arquivo PDF completo.

---

## 🏛️ Certidões Obrigatórias Verificadas

1. **Certidão Federal:** Certidão Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União (Receita Federal / PGFN).
2. **CRF - FGTS:** Certificado de Regularidade do FGTS (Caixa Econômica Federal).
3. **CNDT:** Certidão Negativa de Débitos Trabalhistas (Tribunal Superior do Trabalho / BNDT).
4. **Declaração de Recolhimento do ICMS:** Emitida pela Secretaria de Estado da Fazenda de Sergipe (SEFAZ/SE).
5. **Certidão Negativa Estadual:** Certidão Negativa de Débitos Estaduais (SEFAZ/SE).

---

## 🏢 Regras de Fornecedores Cadastrados

| Fornecedor | CNPJ | Exige Relatório Específico? | Relatório Exigido | Instrução / Aviso |
| :--- | :--- | :--- | :--- | :--- |
| **Prime Benefícios** | `05.340.639/0001-30` (`05340639000130`) | **Sim** | Consumo Subunidade/Veículo | Acesse a aba *Relatórios*. |
| **Bamex Manutenções** | `28.008.410/0001-06` (`28008410000106`) | **Sim** | Manutenções | Acesse *Módulo de manutenção > Ordens de Serviço > Relatórios*. **Aviso obrigatório:** *Antes de gerar o relatório, filtre o status por Finalizada (Somente).* |
| **Demais Fornecedores** | Qualquer outro CNPJ | **Não** | Não aplicável | Não é necessário relatório adicional. |

---

## 🛠️ Arquitetura e Tecnologias

```
projetos-pagamentos/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   │   ├── settings.py             # Configurações globais (limites, OCR, diretórios)
│   │   │   ├── certificate_links.py    # URLs oficiais e metadados das 5 certidões
│   │   │   └── supplier_rules.py       # Registro centralizado de regras de fornecedores
│   │   ├── models/
│   │   │   └── process_db.py           # Modelo SQLAlchemy para histórico no SQLite
│   │   ├── schemas/
│   │   │   ├── certificate.py          # Schemas de certidões e status
│   │   │   ├── supplier.py             # Schemas de fornecedor e candidatos a CNPJ
│   │   │   ├── document.py             # Schemas de atesto, folha de dados e relatórios
│   │   │   └── process.py              # Resposta da análise e resumos
│   │   ├── services/
│   │   │   ├── pdf_extractor.py        # Extração de texto por página via PyMuPDF (fitz)
│   │   │   ├── ocr_service.py          # OCR com Tesseract + PyMuPDF em memória (opcional)
│   │   │   ├── cnpj_service.py         # Normalização, validação matemática e score de contexto
│   │   │   ├── date_service.py         # Extração de datas brasileiras e cálculo de validade
│   │   │   ├── situation_evaluator.py  # Avaliação de situação favorável (negativa vs positiva)
│   │   │   ├── certificate_classifier.py # Classificação multi-sinal e mesclagem de páginas
│   │   │   ├── additional_docs_service.py # Verificação de folha de dados e atesto
│   │   │   ├── instruction_service.py  # Geração dinâmica do checklist de instruções
│   │   │   └── process_analyzer.py     # Orquestrador do pipeline de análise
│   │   ├── routers/
│   │   │   └── processes.py            # Endpoints REST (/api/processes)
│   │   ├── database.py                 # Conexão SQLite
│   │   └── main.py                     # Inicialização do FastAPI e middlewares
│   ├── tests/                          # 29 testes automatizados (pytest)
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── components/                 # Componentes React (Upload, Cards, Badges, Histórico)
│   │   ├── services/                   # Cliente API
│   │   ├── types/                      # Interfaces TypeScript
│   │   ├── App.tsx                     # Aplicação principal
│   │   ├── main.tsx
│   │   └── index.css                   # Tailwind CSS
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── start-backend.ps1                   # Script de inicialização rápida do backend (PowerShell)
├── start-frontend.ps1                  # Script de inicialização rápida do frontend (PowerShell)
└── README.md
```

---

## 🚀 Pré-requisitos

* **Python 3.12+** (ou 3.13) instalado e no PATH.
* **Node.js 18+** (ou 20+) e **npm** instalados.
* *(Opcional)* **Tesseract-OCR** se desejar OCR para páginas escaneadas/digitalizadas no Windows.

---

## ⚡ Como Executar no Windows (PowerShell)

### 1. Iniciar o Backend

Abra um terminal PowerShell na pasta do projeto e execute:

```powershell
.\start-backend.ps1
```

Ou manualmente:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

O backend estará ativo em: `http://127.0.0.1:8000`
A documentação interativa Swagger fica em: `http://127.0.0.1:8000/docs`

---

### 2. Iniciar o Frontend

Abra outro terminal PowerShell na pasta do projeto e execute:

```powershell
.\start-frontend.ps1
```

Ou manualmente:
```powershell
cd frontend
npm install
npm run dev
```

Abra seu navegador em: **`http://localhost:5173`**

---

## 🧪 Como Rodar os Testes Automatizados

O backend possui uma suíte completa com **29 testes automatizados** cobrindo todas as regras de negócio:

```powershell
cd backend
.\.venv\Scripts\pytest -v
```

Os testes incluem:
* Normalização e validação matemática de dígitos verificadores do CNPJ.
* Identificação e ranking de candidatos a CNPJ com pesos contextuais.
* Extração de datas brasileiras (numéricas, por extenso e transições de mês/ano).
* Cálculo de validade relativa (ex: *válida por 180 dias*).
* Classificação multi-sinal das 5 certidões obrigatórias.
* Resistência a falsos positivos (menções em índices/despachos sem certidão real).
* Regra específica do fornecedor **Prime Benefícios**.
* Regra específica do fornecedor **Bamex Manutenções** (incluindo o filtro obrigatório *Finalizada (Somente)*).
* Regra padrão para fornecedores comuns.
* Detecção de certidões vencidas, divergências de CNPJ e documentos ausentes.
* Verificação da folha de dados bancários e termo de atesto.
* Geração do checklist dinâmico de pendências.
* Testes de integração dos endpoints da API REST com SQLite em memória.

---

## 🔍 Configuração do OCR (Opcional)

A aplicação utiliza nativamente o **PyMuPDF** para extração direta e ultrarrápida do texto em PDFs pesquisáveis (que representam a grande maioria dos processos digitais).

Se você receber PDFs que contenham **páginas digitalizadas como imagem pura**:
1. Baixe o instalador do Tesseract para Windows em: [UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki).
2. Instale no caminho padrão (`C:\Program Files\Tesseract-OCR\tesseract.exe`) marcando o pacote de idioma em Português.
3. A aplicação detectará automaticamente o executável do Tesseract sem necessidade de nenhuma configuração adicional.
4. Caso o Tesseract não esteja instalado e o PDF possua páginas digitalizadas, a aplicação alertará claramente o usuário:
   > *"Este PDF parece conter páginas digitalizadas e algumas informações não puderam ser analisadas automaticamente. Faça a conferência manual ou configure o OCR."*

---

## ➕ Como Adicionar um Novo Fornecedor com Regra Específica

Todas as regras de fornecedores ficam centralizadas em um único arquivo:
[`backend/app/config/supplier_rules.py`](file:///backend/app/config/supplier_rules.py)

Para cadastrar um novo fornecedor, basta adicionar uma nova entrada no dicionário `SUPPLIER_RULES_REGISTRY` usando o CNPJ com 14 dígitos (apenas números):

```python
SUPPLIER_RULES_REGISTRY["12345678000199"] = SupplierRule(
    cnpj="12345678000199",
    display_name="Nome da Empresa",
    report_required=True,
    report_name="Nome do Relatório Exigido",
    instructions="Instruções passo a passo para emissão no sistema interno.",
    warnings=["Avisos ou filtros obrigatórios a serem observados."],
)
```

---

## 🌐 Como Alterar os Links Oficiais das Certidões

Os links externos e órgãos emissores das 5 certidões estão centralizados em:
[`backend/app/config/certificate_links.py`](file:///backend/app/config/certificate_links.py)

URLs oficiais cadastradas:
* **Certidão Federal (Receita Federal / PGFN):** `https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/PJ/Emitir`
* **CRF - FGTS (CAIXA):** `https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf`
* **CNDT (TST):** `https://cndt-certidao.tst.jus.br/inicio.faces`
* **Declaração de Recolhimento do ICMS (SEFAZ Sergipe):** `https://www.sefaz.se.gov.br/SitePages/servico.aspx?cod=10`
* **Certidão Negativa Estadual (SEFAZ Sergipe):** `https://www.sefaz.se.gov.br/SitePages/certidoes.aspx`

---

## ⚠️ Limitações Conhecidas

1. **Ferramenta de Auxílio:** A aplicação foi desenhada para agilizar a conferência, mas **não substitui o julgamento humano**. O checklist orienta e aponta pendências para validação pelo operador.
2. **PDFs Escaneados de Baixa Resolução:** Páginas digitalizadas dependem do Tesseract OCR local. Textos manuscritos ou com baixa nitidez podem requerer conferência manual.
3. **Sites Governamentais:** Por razões de conformidade e segurança, a aplicação **não quebra CAPTCHAs nem realiza emissão automática desautorizada**. Ela direciona o operador com um clique para a tela oficial correta e facilita a cópia do CNPJ normalizado.
