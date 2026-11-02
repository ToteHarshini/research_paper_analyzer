import uuid
from datetime import datetime, timezone, timedelta
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from src.db.database import (
    Base,
    configure_database,
    get_db,
    get_db_context,
)
from src.db.models import User, Paper, Conversation, Message, Citation
from src.db.crud import (
    create_user,
    get_user_by_email,
    authenticate_user,
    create_paper,
    get_paper,
    get_user_papers,
    create_conversation,
    get_user_conversations,
    create_message,
    get_conversation_messages,
    create_citation,
    get_paper_citations,
)
from src.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_jwt_secret_key,
    get_jwt_algorithm,
)
from src.db.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    PaperCreate,
    PaperResponse,
    ResearchQueryRequest,
    ResearchQueryResponse,
    ClaimVerification,
    StructuredFinding,
)


# ---------------------------------------------------------------------------
# FIXTURE: IN-MEMORY SQLITE DATABASE
# ---------------------------------------------------------------------------

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Sets up an in-memory SQLite database session with all ORM models."""
    test_engine = sa.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


# ---------------------------------------------------------------------------
# 1. DATABASE MODELS & CRUD VALIDATION
# ---------------------------------------------------------------------------

def test_user_creation_and_authentication(db_session):
    user = create_user(
        db=db_session,
        email="Researcher@Example.Com",
        password="SecurePassword123!",
        full_name="Dr. Jane Doe"
    )
    assert user.id is not None
    assert user.email == "researcher@example.com"
    assert user.full_name == "Dr. Jane Doe"
    assert user.is_active is True

    # Test lookup
    fetched = get_user_by_email(db_session, "researcher@example.com")
    assert fetched is not None
    assert fetched.id == user.id

    # Test authentication
    auth_success = authenticate_user(db_session, "researcher@example.com", "SecurePassword123!")
    assert auth_success is not None
    assert auth_success.id == user.id

    auth_fail = authenticate_user(db_session, "researcher@example.com", "WrongPassword!")
    assert auth_fail is None


def test_paper_and_citation_operations(db_session):
    user = create_user(db_session, "author@example.com", "Password123!")

    paper = create_paper(
        db=db_session,
        user_id=user.id,
        title="Attention Is All You Need",
        filename="attention.pdf",
        authors=["Vaswani et al."],
        abstract="The Transformer architecture.",
        file_path="/data/attention.pdf",
        page_count=15
    )
    assert paper.id is not None
    assert paper.user_id == user.id
    assert paper.title == "Attention Is All You Need"
    assert paper.processing_status == "uploaded"

    user_papers = get_user_papers(db_session, user.id)
    assert len(user_papers) == 1

    fetched_paper = get_paper(db_session, paper.id, user.id)
    assert fetched_paper is not None
    assert fetched_paper.title == paper.title

    # Create citation
    citation = create_citation(
        db=db_session,
        paper_id=paper.id,
        passage_text="Self-attention mechanism connects sequence positions.",
        page_number=3,
        section="Methodology",
        metadata_json={"chunk_id": "P01_C0003"}
    )
    assert citation.id is not None
    assert citation.paper_id == paper.id

    citations = get_paper_citations(db_session, paper.id)
    assert len(citations) == 1
    assert citations[0].section == "Methodology"


def test_conversation_and_message_operations(db_session):
    user = create_user(db_session, "user2@example.com", "Password123!")

    conv = create_conversation(db_session, user_id=user.id, title="Research on Transformers")
    assert conv.id is not None
    assert conv.title == "Research on Transformers"

    conversations = get_user_conversations(db_session, user.id)
    assert len(conversations) == 1

    msg_user = create_message(db_session, conv.id, role="user", content="Explain attention.")
    msg_ai = create_message(db_session, conv.id, role="assistant", content="Attention connects positions.")

    assert msg_user.role == "user"
    assert msg_ai.role == "assistant"

    messages = get_conversation_messages(db_session, conv.id)
    assert len(messages) == 2
    assert messages[0].content == "Explain attention."
    assert messages[1].content == "Attention connects positions."


# ---------------------------------------------------------------------------
# 2. SESSION MANAGEMENT & CONFIGURATION SAFETY
# ---------------------------------------------------------------------------

def test_missing_database_url_safety():
    """Verify missing database engine raises a clean RuntimeError on access, not import."""
    import src.db.database as db_mod
    original_session_local = db_mod.SessionLocal
    db_mod.SessionLocal = None

    try:
        with pytest.raises(RuntimeError, match="DATABASE_URL not found"):
            next(get_db())

        with pytest.raises(RuntimeError, match="DATABASE_URL not found"):
            with get_db_context():
                pass
    finally:
        db_mod.SessionLocal = original_session_local


def test_configure_database_dynamic():
    """Test dynamic database engine reconfiguration (e.g. for testing)."""
    engine = configure_database("sqlite:///:memory:")
    assert engine is not None
    with get_db_context() as session:
        result = session.execute(sa.text("SELECT 1")).scalar()
        assert result == 1


# ---------------------------------------------------------------------------
# 3. AUTHENTICATION & SECURITY (PASSWORD HASHING & JWT)
# ---------------------------------------------------------------------------

@pytest.fixture(name="jwt_test_secret")
def fixture_jwt_test_secret(monkeypatch):
    """Sets a temporary random secret key and valid algorithm for JWT testing."""
    test_key = "test-secret-key-that-is-at-least-32-bytes-long!"
    monkeypatch.setenv("JWT_SECRET_KEY", test_key)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    return test_key


def test_argon2_password_hashing():
    password = "MyStrongPassword$2026"
    hashed = hash_password(password)

    assert hashed != password
    assert "$argon2" in hashed
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False


def test_jwt_token_lifecycle(jwt_test_secret):
    user_id = str(uuid.uuid4())
    email = "researcher@domain.org"

    token = create_access_token(
        data={"sub": user_id, "email": email},
        expires_delta=timedelta(minutes=30)
    )
    assert isinstance(token, str)
    assert len(token) > 20

    # Decode and validate
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_token_expired(jwt_test_secret):
    user_id = str(uuid.uuid4())
    # Create already-expired token
    expired_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(seconds=-10)
    )
    payload = decode_access_token(expired_token)
    assert payload is None


def test_jwt_invalid_token(jwt_test_secret):
    assert decode_access_token("not-a-valid-token") is None


def test_jwt_missing_secret_raises_runtime_error(monkeypatch):
    """Verify that creating or decoding tokens without JWT_SECRET_KEY raises a clear RuntimeError."""
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not configured"):
        create_access_token(data={"sub": "user-123"})

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY is not configured"):
        decode_access_token("some.test.token")


def test_jwt_insecure_algorithm_rejected(monkeypatch):
    """Verify that insecure or unauthorized JWT algorithms are explicitly rejected."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-bytes-long!")
    monkeypatch.setenv("JWT_ALGORITHM", "none")

    with pytest.raises(ValueError, match="Unsupported or insecure JWT algorithm"):
        create_access_token(data={"sub": "user-123"})


def test_jwt_module_import_without_secret(monkeypatch):
    """Verify that the security module imports without error when JWT_SECRET_KEY is unset."""
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    import importlib
    import src.auth.security as sec
    importlib.reload(sec)
    assert sec is not None


# ---------------------------------------------------------------------------
# 4. PYDANTIC SCHEMA VALIDATION
# ---------------------------------------------------------------------------

def test_pydantic_user_schemas():
    user_data = UserCreate(email="Test@Example.com", password="SecurePassword123")
    assert user_data.email == "test@example.com"  # Normalized to lower-case
    assert user_data.password == "SecurePassword123"

    with pytest.raises(Exception):
        UserCreate(email="invalid-email", password="123")  # Too short and invalid email

    user_resp = UserResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    assert user_resp.is_active is True


def test_pydantic_paper_schemas():
    paper_req = PaperCreate(
        title="Test Paper",
        filename="test.pdf",
        authors=["Author A", "Author B"],
        page_count=10
    )
    assert paper_req.title == "Test Paper"
    assert len(paper_req.authors) == 2


def test_pydantic_research_query_schemas():
    query = ResearchQueryRequest(question="What are the findings?")
    assert query.question == "What are the findings?"
    assert query.paper_ids is None

    with pytest.raises(Exception):
        ResearchQueryRequest(question="ab")  # min_length=3

    response = ResearchQueryResponse(
        question="What are the findings?",
        subquestions=["Subq 1"],
        final_report="# Report",
        verified_claims=[
            ClaimVerification(
                claim="Claim A",
                status="supported",
                reason="Found in text",
                citations=["P01_C0001"]
            )
        ],
        structured_findings=[
            StructuredFinding(
                category="models",
                finding="Transformer Model",
                sources=[{"citation_id": "P01_C0001"}]
            )
        ]
    )
    assert len(response.verified_claims) == 1
    assert response.verified_claims[0].status == "supported"
    assert response.structured_findings[0].category == "models"
