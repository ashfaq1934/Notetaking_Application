from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, create_engine, ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    password = Column(String(200), nullable=False)


class Collection(Base):
    __tablename__ = 'collection'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    uuid = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    public = Column(Boolean, nullable=False)


class Flashcard(Base):
    __tablename__ = 'flashcard'
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collection.id'), nullable=False)
    uuid = Column(String(200), unique=True, nullable=False)
    term = Column(String(200), nullable=False)
    definition = Column(Text, nullable=True)
    public = Column(Boolean, nullable=False)
    edited = Column(DateTime, nullable=False)


class Note(Base):
    __tablename__ = 'note'
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collection.id'), nullable=False)
    uuid = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    public = Column(Boolean, nullable=False)
    edited = Column(DateTime, nullable=False)


engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)
