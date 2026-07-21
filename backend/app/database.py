from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = (
    {"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {}
)

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_database() -> None:
    # Import models so SQLAlchemy registers all mapped classes before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    apply_lightweight_migrations()


def apply_lightweight_migrations() -> None:
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return

    product_columns = {column["name"] for column in inspector.get_columns("products")}
    if "purchase_price" in product_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE products ADD COLUMN purchase_price NUMERIC(10, 2)")
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
