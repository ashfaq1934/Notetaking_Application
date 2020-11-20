from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, create_engine, ForeignKey
from dotenv import load_dotenv
import os


load_dotenv()
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


class Deck(Base):
    __tablename__ = 'deck'
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collection.id'), nullable=False)
    uuid = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    public = Column(Boolean, nullable=False)
    edited = Column(DateTime, nullable=False)


class Flashcard(Base):
    __tablename__ = 'flashcard'
    id = Column(Integer, primary_key=True)
    deck_id = Column(Integer, ForeignKey('deck.id'), nullable=False)
    uuid = Column(String(200), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    term = Column(Text, nullable=True)
    definition = Column(Text, nullable=True)
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


if os.getenv('ENVIRONMENT') == 'testing' or os.getenv('ENVIRONMENT') == 'live':
    db_host = os.getenv("DATABASE_HOST")
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")
    db_name = os.getenv("DATABASE_NAME")
    db_port = os.getenv("DATABASE_PORT")
    engine = create_engine('mysql+pymysql://' + db_user + ':' + db_password + '@' + db_host + '/' + db_name)
else:
    engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
