"""Routes HTML et API JSON de SecureNotes."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from . import db

bp = Blueprint("main", __name__)

MAX_TITLE = 120
MAX_CONTENT = 2000


def _validate(title, content):
    title = (title or "").strip()
    content = (content or "").strip()
    if not title or not content:
        return None, "Le titre et le contenu sont obligatoires."
    if len(title) > MAX_TITLE or len(content) > MAX_CONTENT:
        return None, "Titre ou contenu trop long."
    return (title, content), None


@bp.get("/")
def index():
    return render_template("index.html", notes=db.list_notes(), error=None)


@bp.post("/notes")
def create_note_form():
    data, error = _validate(request.form.get("title"), request.form.get("content"))
    if error:
        return render_template("index.html", notes=db.list_notes(), error=error), 400
    db.create_note(*data)
    return redirect(url_for("main.index"))


@bp.get("/notes/<int:note_id>")
def show_note(note_id):
    note = db.get_note(note_id)
    if note is None:
        abort(404)
    return render_template("note.html", note=note)


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.get("/api/notes")
def api_list_notes():
    return jsonify([dict(n) for n in db.list_notes()])


@bp.get("/api/notes/<int:note_id>")
def api_get_note(note_id):
    note = db.get_note(note_id)
    if note is None:
        return jsonify(error="Note introuvable"), 404
    return jsonify(dict(note))


@bp.post("/api/notes")
def api_create_note():
    payload = request.get_json(silent=True) or {}
    data, error = _validate(payload.get("title"), payload.get("content"))
    if error:
        return jsonify(error=error), 400
    note_id = db.create_note(*data)
    return jsonify(dict(db.get_note(note_id))), 201


# ---------------------------------------------------------------------------
# Nouvelle fonctionnalité : recherche, diagnostic réseau et import YAML
# ---------------------------------------------------------------------------
import subprocess  # noqa: E402

import yaml  # noqa: E402
from markupsafe import Markup  # noqa: E402


@bp.get("/search")
def search():
    q = request.args.get("q", "")
    conn = db.get_db()
    try:
        # VULNÉRABLE (CWE-89) : requête SQL construite par concaténation
        rows = conn.execute(
            f"SELECT id, title, content FROM notes WHERE title LIKE '%{q}%' OR content LIKE '%{q}%'"
        ).fetchall()
    except Exception as exc:  # VULNÉRABLE (CWE-209) : erreur SQL renvoyée au client
        return f"<h2>Erreur</h2><pre>sqlite3.OperationalError: {exc}</pre>", 500
    items = "".join(f"<li>{r['title']}</li>" for r in rows)
    # VULNÉRABLE (CWE-79) : saisie utilisateur réinjectée sans échappement
    return render_template("search.html", query=Markup(q), results=Markup(items))


@bp.get("/admin/ping")
def admin_ping():
    # VULNÉRABLE (CWE-306 + CWE-78) : route d'administration sans authentification
    # et injection de commande via shell=True
    host = request.args.get("host", "127.0.0.1")
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True, text=True)
    return f"<pre>{result.stdout}{result.stderr}</pre>"


@bp.post("/api/notes/import")
def api_import_notes():
    # VULNÉRABLE (CWE-502) : désérialisation YAML non sûre (yaml.Loader instancie des objets Python)
    data = yaml.load(request.get_data(as_text=True), Loader=yaml.Loader)
    created = [db.create_note(n["title"], n["content"]) for n in data]
    return jsonify(imported=len(created)), 201
