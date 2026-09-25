import os
import shutil
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("pocketsmart.database")

# Resolve and normalize database URL
db_url = (settings.DATABASE_URL or "").strip()
if not db_url:
    db_url = "sqlite:///./pocketsmart.db"

# Handle legacy postgres:// URLs (common in Heroku / Supabase)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# In Vercel serverless environment, the root directory is read-only
# If SQLite is being used as fallback, copy db to /tmp so it is writable
if os.environ.get("VERCEL") and db_url.startswith("sqlite"):
    tmp_db_path = Path("/tmp/pocketsmart.db")
    src_db_path = Path(__file__).resolve().parent.parent.parent / "pocketsmart.db"
    if not tmp_db_path.exists() and src_db_path.exists():
        try:
            shutil.copy2(src_db_path, tmp_db_path)
            logger.info("Copied SQLite DB to /tmp for Vercel writable access")
        except Exception as e:
            logger.warning(f"Could not copy SQLite DB to /tmp: {e}")
    db_url = f"sqlite:///{tmp_db_path.as_posix()}"

# Configure engine arguments
connect_args = {}
engine_kwargs = {"echo": False}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL / MySQL serverless pool management
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

def _build_engine(url: str, kwargs: dict):
    """Build engine with driver fallback if needed."""
    try:
        return create_engine(url, **kwargs)
    except Exception as exc:
        logger.warning(f"Failed to create engine with primary URL: {exc}")
        # If psycopg3 failed, try psycopg2 or vice-versa
        if "postgresql+psycopg://" in url:
            alt_url = url.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)
            logger.info("Falling back to postgresql+psycopg2 driver")
            return create_engine(alt_url, **kwargs)
        elif "postgresql://" in url and not url.startswith("postgresql+"):
            alt_url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            logger.info("Trying explicit postgresql+psycopg2 driver")
            return create_engine(alt_url, **kwargs)
        raise

engine = _build_engine(db_url, engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency that yields a database session and closes it afterwards."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes tables in the database and seeds demo user if absent."""
    import app.models.user  # noqa: F401
    import app.models.recommendation  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return

    # Seed demo user
    try:
        db = SessionLocal()
        try:
            from app.models.user import User
            from app.core.security import get_password_hash
            demo = db.query(User).filter(User.email == "alex.demo@pocketsmart.ai").first()
            if not demo:
                demo_user = User(
                    name="Alex Morgan",
                    email="alex.demo@pocketsmart.ai",
                    password_hash=get_password_hash("PocketSmart2026!")
                )
                db.add(demo_user)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not seed demo user: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not open session for demo user seed: {e}")
