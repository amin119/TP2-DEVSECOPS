# Image d'exécution durcie de SecureNotes
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_PATH=/app/data/securenotes.db

# Correctifs de sécurité du système de base
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# setuptools fourni par l'image de base est vulnérable (CVE-2025-47273, détectée par Trivy)
# et inutile à l'exécution : il est supprimé de l'image.
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && (pip uninstall -y setuptools wheel || true)
RUN find / -xdev \( -iname "setuptools*" \) -not -path "/proc/*" 2>/dev/null || true

COPY app ./app
COPY wsgi.py .

# Exécution sous un utilisateur non privilégié
RUN useradd --system --uid 10001 --home /app appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "wsgi:app"]
