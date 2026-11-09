# SecureNotes – TP2 DevSecOps : sécurité intégrée au pipeline CI/CD

Petite application Flask (prise de notes + API JSON) servant de support au TP2.
Le pipeline GitHub Actions (`.github/workflows/ci.yml`) agit comme **garde-fou de sécurité** :

| Job | Outil(s) | Règle bloquante |
|---|---|---|
| Build & tests | flake8, pytest, pytest-cov | lint ou test en échec |
| SAST | Semgrep (p/python, p/flask, p/owasp-top-ten), Bandit | sévérité ERROR/HIGH (Semgrep), HIGH (Bandit) |
| Secrets | Gitleaks | tout secret détecté |
| SCA | Trivy (fs + image), pip-audit (informatif) | CVE HIGH ou CRITICAL |
| DAST | OWASP ZAP full scan sur environnement éphémère (conteneur Docker) | alerte de risque High |
| Security gate | agrégation | un des jobs ci-dessus en échec |
| Deploy | push de l'image vers GHCR | uniquement sur `main` et si la gate passe |

## Lancer en local

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=app
docker build -t securenotes . && docker run -p 8000:8000 securenotes
```

Le rapport du TP (LaTeX, en français) se trouve dans `rapport/`.
