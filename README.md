# Conferência de Processos de Pagamento

Aplicação web completa, funcional e **100% stateless** desenvolvida para auxiliar na conferência e auditoria de processos administrativos de pagamento de fornecedores, pronta para deploy no **Railway** via Docker.

O sistema recebe o processo em PDF, extrai o texto página a página via **PyMuPDF**, executa OCR com **Tesseract (Português)** em páginas digitalizadas quando necessário, identifica fornecedores e CNPJ, valida as cinco certidões obrigatórias, confere documentos complementares (folha de dados bancários e atesto), aplica regras específicas de relatórios por fornecedor e apresenta um checklist claro com links oficiais diretos para emissão de certidões ausentes ou vencidas.

---

## 🔒 Arquitetura Stateless e Privacidade

* **Sem Banco de Dados e Sem Histórico:** A aplicação não armazena registros, histórico ou metadados após a resposta da requisição.
* **Arquivos Temporários Efêmeros:** O PDF é processado e imediatamente excluído do disco no bloco `finally`.
* **Sem APIs Externas:** Não há envio de documentos para Gemini, OpenAI ou qualquer serviço em nuvem de terceiros.
* **Sem Autenticação:** Acesso direto e descomplicado para uso em estações de trabalho e navegadores.

---

## 🏛️ Certidões Obrigatórias Verificadas

1. **Certidão Federal:** Certidão Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União (Receita Federal / PGFN).
2. **CRF - FGTS:** Certificado de Regularidade do FGTS (Caixa Econômica Federal).
3. **CNDT:** Certidão Negativa de Débitos Trabalhistas (Tribunal Superior do Trabalho / BNDT).
4. **Declaração de Recolhimento do ICMS:** Emitida pela Secretaria de Estado da Fazenda de Sergipe (SEFAZ/SE).
5. **Certidão Negativa Estadual:** Certidão Negativa de Débitos Estaduais (SEFAZ/SE).

---

## 🚀 Deploy no Railway (Passo a Passo)

A aplicação foi configurada com um `Dockerfile` multi-stage na raiz do projeto, unificando o frontend React compilado, o backend FastAPI e o Tesseract OCR em um **único serviço web**.

### Pré-requisitos
1. Conta no [GitHub](https://github.com/) com este repositório sincronizado.
2. Conta no [Railway](https://railway.app/).

### Passo a passo no painel do Railway:
1. Acesse seu painel no **[Railway Dashboard](https://railway.app/dashboard)**.
2. Clique no botão **`+ New Project`**.
3. Selecione a opção **`Deploy from GitHub repo`**.
4. Escolha o repositório **`conferencia-processos-pagamento`**.
5. O Railway detectará automaticamente o `Dockerfile` na raiz e iniciará o build multi-stage (Node para compilar o React + Python/Tesseract para o container final).
6. Nas configurações do serviço (**Settings**):
   * **Healthcheck Path:** Configure para `/api/health`.
   * **Port:** O Railway define automaticamente a variável `$PORT` (o FastAPI já está configurado para escutar `0.0.0.0:${PORT:-8000}`).
7. Na aba **Settings > Networking**, clique em **`Generate Domain`** para criar a URL pública (ex: `https://conferencia-processos.up.railway.app`).
8. Acesse a URL gerada pelo navegador!

---

## 💻 Desenvolvimento e Execução Local

### Opção 1: Scripts PowerShell Rápidos (Windows)

1. **Backend:** Abra o PowerShell e execute:
   ```powershell
   .\start-backend.ps1
   ```
   > Servidor FastAPI ativo em `http://127.0.0.1:8000` (docs em `/docs` e health check em `/api/health`).

2. **Frontend:** Em outro terminal, execute:
   ```powershell
   .\start-frontend.ps1
   ```
   > Interface React Vite ativa em `http://localhost:5173`.

---

## 🧪 Testes Automatizados

O projeto possui **29 testes automatizados** cobrindo todas as regras de negócio, extração de texto, validação de datas, módulos matemáticos de CNPJ e endpoints REST:

```powershell
cd backend
.\.venv\Scripts\pytest -v
```

---

## 🔍 OCR e Extração de Texto

1. **Extração Nativa (PyMuPDF):** É executada prioritariamente em todas as páginas por ser extremamente rápida e precisa em PDFs pesquisáveis.
2. **OCR Seletivo (Tesseract):** Somente páginas com quantidade de caracteres abaixo do limite configurável são renderizadas e enviadas para o Tesseract, otimizando o consumo de CPU/memória.
3. **Container de Produção:** O `Dockerfile` inclui nativamente os pacotes `tesseract-ocr` e `tesseract-ocr-por` (suporte ao idioma português).
4. **Resiliência:** Caso ocorra falha de OCR em uma página específica, a aplicação registra o aviso e continua processando as demais páginas normalmente.

---

## ⚠️ Limitações e Recomendações

1. **Ferramenta de Apoio:** A aplicação não substitui o julgamento humano. Ela aponta pendências e divergências de forma automatizada para conferência do operador.
2. **Emissão de Certidões:** A aplicação direciona para as páginas oficiais estáveis e facilita a cópia do CNPJ normalizado, sem tentar contornar proteções governamentais ou CAPTCHAs.
