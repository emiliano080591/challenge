from fastapi.testclient import TestClient

def _get_text(item: dict) -> str:
    # Normaliza: acepta "message" o "content"
    return item.get("message") if "message" in item else item.get("content", "")

def test_chat_starts_conversation(client: TestClient):
    payload = {"conversation_id": None, "message": "Topic: Espacio; Stance: Duda"}
    r = client.post("/api/chat", json=payload)
    assert r.status_code == 200, r.text

    data = r.json()
    assert "conversation_id" in data
    assert isinstance(data["message"], list)
    assert len(data["message"]) >= 2  # user + bot

    roles = [m["role"] for m in data["message"]]
    assert "user" in roles and "bot" in roles

    # Estructura homogénea: role + (message|content)
    for item in data["message"]:
        assert "role" in item
        assert "message" in item or "content" in item
        assert isinstance(_get_text(item), str)

    bot_msg = next(m for m in data["message"] if m["role"] == "bot")
    assert "RESPUESTA_MOCK" in _get_text(bot_msg)

def test_chat_continue_conversation(client: TestClient):
    r1 = client.post("/api/chat", json={"conversation_id": None, "message": "Topic: X; Stance: Y"})
    assert r1.status_code == 200, r1.text
    cid = r1.json()["conversation_id"]

    r2 = client.post("/api/chat", json={"conversation_id": cid, "message": "otro turno"})
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["conversation_id"] == cid
    assert len(data["message"]) == 4
