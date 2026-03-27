from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./complaints.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, unique=True, index=True)

    # Original input
    original_text = Column(Text)
    original_language = Column(String)
    input_type = Column(String)          # voice | text | file

    # Processed
    translated_text = Column(Text)
    summary = Column(Text)

    # Classification
    category = Column(String)
    sub_category = Column(String)
    department = Column(String)
    priority = Column(String)            # low | medium | high | urgent
    confidence = Column(Float)

    # Meta
    citizen_name = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, default="submitted")   # submitted | in_review | resolved
    report_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
