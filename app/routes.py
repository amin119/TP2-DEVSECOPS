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
