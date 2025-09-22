import pytest
from sqlalchemy.orm import Session

from app.services.chat import DebateService
from app.domain.schemas import ChatRequest


@pytest.mark.parametrize(
    "first_message,exp_topic,exp_stance",
    [
        ("Topic: Espacio; Stance: La tierra es plana", "Espacio", "La tierra es plana"),
        ("Topic: Política; Stance: El voto obligatorio es necesario", "Política", "El voto obligatorio es necesario"),
        ("Solo texto libre sin formato", "Solo texto libre sin formato", "bot's position"),
    ],
)
def test_parse_topic_and_stance(db_session: Session, stub_llm_ok, first_message, exp_topic, exp_stance):
    svc = DebateService(db=db_session, llm=stub_llm_ok)
    topic, stance = svc._parse_topic_and_stance(first_message)
    assert topic == exp_topic
    assert stance == exp_stance


def test_handle_new_conversation_ok(db_session: Session, stub_llm_ok):
    svc = DebateService(db=db_session, llm=stub_llm_ok)
    payload = ChatRequest(conversation_id=None, message="Topic: Ciencia; Stance: Dudar del alunizaje")
    resp = svc.handle(payload)

    assert resp.conversation_id
    assert len(resp.message) == 2
    assert resp.message[0].role == "user"
    assert resp.message[1].role == "bot"
    assert "RESPUESTA_MOCK" in resp.message[1].message


def test_handle_existing_conversation(db_session: Session, stub_llm_ok):
    svc = DebateService(db=db_session, llm=stub_llm_ok)
    p1 = svc.handle(ChatRequest(conversation_id=None, message="Topic: Ciencia; Stance: X"))
    cid = p1.conversation_id

    resp = svc.handle(ChatRequest(conversation_id=cid, message="Siguiente turno"))

    assert resp.conversation_id == cid
    assert len(resp.message) == 4
    assert resp.message[-1].role == "bot"
    assert isinstance(resp.message[-1].message, str)


def test_llm_failure_propagates(db_session: Session, stub_llm_fail):
    svc = DebateService(db=db_session, llm=stub_llm_fail)
    with pytest.raises(RuntimeError):
        svc.handle(ChatRequest(conversation_id=None, message="Topic: X; Stance: Y"))
