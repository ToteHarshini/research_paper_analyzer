from sqlalchemy import select
from sqlalchemy.orm import Session

from pwdlib import PasswordHash

from src.db.models import (
    User,
    Paper,
    Conversation,
    Message,
    Citation,
)

password_hash = PasswordHash.recommended()


# -------------------------
# USER OPERATIONS
# -------------------------

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str | None = None,
):
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str):
    statement = select(User).where(
        User.email == email.lower().strip()
    )
    return db.scalar(statement)


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user or not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


# -------------------------
# PAPER OPERATIONS
# -------------------------

def create_paper(
    db: Session,
    user_id,
    title: str,
    filename: str,
    authors=None,
    abstract=None,
    file_path=None,
    page_count=None,
):
    paper = Paper(
        user_id=user_id,
        title=title,
        filename=filename,
        authors=authors,
        abstract=abstract,
        file_path=file_path,
        page_count=page_count,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


def get_paper(db: Session, paper_id, user_id):
    statement = select(Paper).where(
        Paper.id == paper_id,
        Paper.user_id == user_id,
    )
    return db.scalar(statement)


def get_user_papers(db: Session, user_id):
    statement = (
        select(Paper)
        .where(Paper.user_id == user_id)
        .order_by(Paper.created_at.desc())
    )
    return list(db.scalars(statement).all())


# -------------------------
# CONVERSATION OPERATIONS
# -------------------------

def create_conversation(
    db: Session,
    user_id,
    title: str | None = None,
):
    conversation = Conversation(
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_user_conversations(db: Session, user_id):
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(db.scalars(statement).all())


# -------------------------
# MESSAGE OPERATIONS
# -------------------------

def create_message(
    db: Session,
    conversation_id,
    role: str,
    content: str,
):
    if role not in {"user", "assistant", "system"}:
        raise ValueError("Invalid message role")

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages(db: Session, conversation_id):
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(db.scalars(statement).all())


# -------------------------
# CITATION OPERATIONS
# -------------------------

def create_citation(
    db: Session,
    paper_id,
    passage_text: str,
    message_id=None,
    page_number=None,
    section=None,
    metadata_json=None,
):
    citation = Citation(
        paper_id=paper_id,
        message_id=message_id,
        passage_text=passage_text,
        page_number=page_number,
        section=section,
        metadata_json=metadata_json,
    )
    db.add(citation)
    db.commit()
    db.refresh(citation)
    return citation


def get_paper_citations(db: Session, paper_id):
    statement = (
        select(Citation)
        .where(Citation.paper_id == paper_id)
        .order_by(Citation.page_number.asc())
    )
    return list(db.scalars(statement).all())
