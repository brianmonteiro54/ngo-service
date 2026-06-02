# =============================================================================
# Stage 1: Builder - Instalação de dependências Python
# =============================================================================
FROM python:3.13-slim AS builder

# Instala dependências do sistema necessárias para compilar pacotes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copia apenas requirements.txt primeiro (melhor cache)
COPY requirements.txt .

# Cria virtualenv e instala dependências
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala automaticamente as instrumentações OTel para as libs presentes
RUN opentelemetry-bootstrap -a install

# =============================================================================
# Stage 2: Final - Imagem de produção mínima
# =============================================================================
FROM python:3.13-slim

# Apenas runtime libs (libpq5 para PostgreSQL, wget para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN groupadd -r -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -m -s /sbin/nologin appuser

# Copia o virtualenv do stage anterior (já com as instrumentações OTel)
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ===== Configuração OpenTelemetry via variáveis de ambiente =====
ENV OTEL_SERVICE_NAME="ngo-service" \
    OTEL_RESOURCE_ATTRIBUTES="service.namespace=solidarytech,deployment.environment=production,service.version=1.0.0" \
    OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317" \
    OTEL_EXPORTER_OTLP_INSECURE="true" \
    OTEL_EXPORTER_OTLP_PROTOCOL="grpc" \
    OTEL_TRACES_EXPORTER="otlp" \
    OTEL_METRICS_EXPORTER="otlp" \
    OTEL_LOGS_EXPORTER="otlp" \
    OTEL_PYTHON_LOG_CORRELATION="true"

WORKDIR /app

# Copia código da aplicação
COPY --chown=appuser:appgroup app.py .
COPY --chown=appuser:appgroup db/ ./db/

USER appuser

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8081/health || exit 1

# Auto-instrumenta o gunicorn com OpenTelemetry
CMD ["opentelemetry-instrument", "gunicorn", "--bind", "0.0.0.0:8081", "--workers", "4", "--timeout", "60", "--access-logfile", "-", "app:app"]
