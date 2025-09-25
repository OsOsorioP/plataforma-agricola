import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

print(repr(SQLALCHEMY_DATABASE_URL))

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Configuraciones importantes para evitar problemas de encoding
    connect_args={
        "client_encoding": "utf8"
    },
    # Configuraciones adicionales
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Cambia a True si quieres ver las queries SQL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_database_if_not_exists():
    try:
        if not database_exists(engine.url):
            print(f"Creating database...")
            create_database(engine.url)
            print(f"Database created successfully")
        else:
            print(f"Database already exists")
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()