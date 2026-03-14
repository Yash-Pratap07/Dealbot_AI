from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./dealbot.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)          # nullable for OAuth users
    # OAuth providers
    google_id = Column(String, unique=True, nullable=True, index=True)
    facebook_id = Column(String, unique=True, nullable=True, index=True)
    # Phone auth
    phone = Column(String, unique=True, nullable=True, index=True)
    phone_verified = Column(Boolean, default=False)
    # Profile
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    auth_provider = Column(String, default="local")          # local | google | facebook | phone
    created_at = Column(DateTime, default=datetime.utcnow)


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    max_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=True)
    agreement = Column(Boolean, default=False)
    contract_hash = Column(String, nullable=True)
    tx_hash = Column(String, nullable=True)
    history = Column(Text, nullable=True)
    # New fields for rich negotiation
    product = Column(String, nullable=True, default="item")
    market_price = Column(Float, nullable=True)
    fraud_flags = Column(Text, nullable=True)   # JSON list of flag strings
    strategy = Column(String, nullable=True, default="balanced")
    rounds_taken = Column(Integer, nullable=True)
    evaluation = Column(Text, nullable=True)    # JSON evaluation dict
    votes = Column(Text, nullable=True)         # JSON votes dict
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe_add_column(conn, table: str, column: str, col_type: str) -> None:
    """Add a column only if it doesn't already exist (SQLite safe)."""
    try:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        conn.commit()
    except Exception:
        pass  # Column already exists — that's fine


def init_db():
    Base.metadata.create_all(bind=engine)
    # Safe-migrate existing databases that predate new columns
    with engine.connect() as conn:
        # deals table
        _safe_add_column(conn, "deals", "product",        "VARCHAR")
        _safe_add_column(conn, "deals", "market_price",   "FLOAT")
        _safe_add_column(conn, "deals", "fraud_flags",    "TEXT")
        _safe_add_column(conn, "deals", "strategy",       "VARCHAR")
        _safe_add_column(conn, "deals", "rounds_taken",   "INTEGER")
        _safe_add_column(conn, "deals", "evaluation",     "TEXT")
        _safe_add_column(conn, "deals", "votes",          "TEXT")
        # users table — OAuth / phone auth columns
        _safe_add_column(conn, "users", "google_id",      "VARCHAR")
        _safe_add_column(conn, "users", "facebook_id",    "VARCHAR")
        _safe_add_column(conn, "users", "phone",          "VARCHAR")
        _safe_add_column(conn, "users", "phone_verified", "BOOLEAN DEFAULT 0")
        _safe_add_column(conn, "users", "display_name",   "VARCHAR")
        _safe_add_column(conn, "users", "avatar_url",     "VARCHAR")
        _safe_add_column(conn, "users", "auth_provider",  "VARCHAR DEFAULT 'local'")
