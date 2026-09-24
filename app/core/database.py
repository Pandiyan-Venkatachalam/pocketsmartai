from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

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
    Base.metadata.create_all(bind=engine)

    # Seed demo user
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
    finally:
        db.close()
