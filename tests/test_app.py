import re


def _csrf(client):
    html = client.get("/").get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_lists_seed_notes(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Bienvenue" in resp.get_data(as_text=True)


def test_security_headers_present(client):
    resp = client.get("/")
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_api_create_and_get_note(client):
    resp = client.post("/api/notes", json={"title": "Test", "content": "Contenu"})
    assert resp.status_code == 201
    note_id = resp.get_json()["id"]
    resp = client.get(f"/api/notes/{note_id}")
    assert resp.get_json()["title"] == "Test"


def test_api_rejects_invalid_payload(client):
    assert client.post("/api/notes", json={"title": ""}).status_code == 400
    assert client.post("/api/notes", json={"title": "x" * 500, "content": "y"}).status_code == 400


def test_api_unknown_note_returns_404(client):
    assert client.get("/api/notes/9999").status_code == 404


def test_form_requires_csrf_token(client):
    resp = client.post("/notes", data={"title": "a", "content": "b"})
    assert resp.status_code == 400


def test_form_with_csrf_token_creates_note(client):
    token = _csrf(client)
    resp = client.post("/notes", data={"title": "Form", "content": "ok", "csrf_token": token})
    assert resp.status_code == 302
    assert "Form" in client.get("/").get_data(as_text=True)


def test_note_content_is_html_escaped(client):
    payload = "<script>alert(1)</script>"
    note_id = client.post("/api/notes", json={"title": payload, "content": payload}).get_json()["id"]
    html = client.get(f"/notes/{note_id}").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_search_finds_note(client):
    resp = client.get("/search?q=Bienvenue")
    assert resp.status_code == 200
    assert "Bienvenue" in resp.get_data(as_text=True)


def test_import_yaml_notes(client):
    body = "- title: Import\n  content: depuis YAML\n"
    resp = client.post("/api/notes/import", data=body, content_type="application/x-yaml")
    assert resp.status_code == 201
    assert resp.get_json() == {"imported": 1}
