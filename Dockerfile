# ========================================================
# Stage 1: Build Frontend (React + Vite + TypeScript)
# ========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# ========================================================
# Stage 2: Python Backend with Tesseract OCR & PyMuPDF
# ========================================================
FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies: Tesseract OCR + Portuguese language pack
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set workdir to backend directory so app.main:app is directly importable
WORKDIR /app/backend

# Expose port (overridden dynamically by Railway PORT variable)
EXPOSE 8000

# Start FastAPI server listening on 0.0.0.0 and PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
