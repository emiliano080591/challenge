from sqlalchemy.orm import Session
from app.respositories.sql import ConversationRepository, MessageRepository


def test_conversation_create_and_get(db_session: Session):
    convs = ConversationRepository(db_session)
    conv = convs.create(topic="T1", stance="S1")
    db_session.flush()
    cid = conv.id

    got = convs.get(cid)
    assert got is not None
    assert got.id == cid
    assert got.topic == "T1"
    assert got.stance == "S1"


def test_messages_add_and_last_n(db_session: Session):
    convs = ConversationRepository(db_session)
    msgs = MessageRepository(db_session)
    conv = convs.create(topic="T", stance="S")
    db_session.flush()

    msgs.add(conv, role="user", content="u1")
    msgs.add(conv, role="bot", content="b1")
    msgs.add(conv, role="user", content="u2")
    msgs.add(conv, role="bot", content="b2")
    db_session.flush()

    last = msgs.last_n(conv.id, n=3)
    assert [m.content for m in last] == ["b1", "u2", "b2"]
