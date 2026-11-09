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
# pip embarque une copie de setuptools 70.3.0 (pkg_resources) vulnérable à CVE-2025-47273,
# détectée par Trivy. pip est inutile à l'exécution : il est retiré de l'image finale.
RUN pip install -r requirements.txt \
    && python -m pip uninstall -y pip

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
