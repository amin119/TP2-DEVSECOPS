"""Accès SQLite - toutes les requêtes sont paramétrées."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            [
                ("Bienvenue", "Première note de SecureNotes."),
                ("DevSecOps", "La sécurité est intégrée dès le pipeline CI/CD."),
            ],
        )
        conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)


def list_notes():
    return get_db().execute(
        "SELECT id, title, content, created_at FROM notes ORDER BY id DESC"
    ).fetchall()


def get_note(note_id):
    return get_db().execute(
        "SELECT id, title, content, created_at FROM notes WHERE id = ?", (note_id,)
    ).fetchone()


def create_note(title, content):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)", (title, content)
    )
    conn.commit()
    return cur.lastrowid
