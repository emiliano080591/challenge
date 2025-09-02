from fastapi.testclient import TestClient


def test_chat_starts_conversation(client: TestClient):
    payload = {"conversation_id": None, "message": "Topic: Espacio; Stance: Duda"}
    r = client.post("/api/chat", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert "conversation_id" in data
    assert isinstance(data["message"], list)
    assert len(data["message"]) >= 2

    roles = [m["role"] for m in data["message"]]
    assert "user" in roles
    assert "bot" in roles

    bot_msg = next(m for m in data["message"] if m["role"] == "bot")

    text = bot_msg.get("message") if "message" in bot_msg else bot_msg.get("content")
    assert isinstance(text, str)
    assert "RESPUESTA_MOCK" in text


def test_chat_continue_conversation(client: TestClient):
    r1 = client.post("/api/chat", json={"conversation_id": None, "message": "Topic: X; Stance: Y"})
    assert r1.status_code == 200
    cid = r1.json()["conversation_id"]

    r2 = client.post("/api/chat", json={"conversation_id": cid, "message": "otro turno"})
    assert r2.status_code == 200
    data = r2.json()
    assert data["conversation_id"] == cid
    assert len(data["message"]) == 4
