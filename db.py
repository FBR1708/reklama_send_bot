from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("postgresql://postgres:1@localhost:5433/reklama")
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Advertisement(Base):
    __tablename__ = "advertisement"

    id = Column(Integer, primary_key=True)
    title = Column(String(length=255))
    body = Column(Text())
    file_id = Column(Text())
