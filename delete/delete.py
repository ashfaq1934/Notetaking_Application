from flask import Blueprint, redirect, url_for, flash, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from authentication.auth import requires_login
from dotenv import load_dotenv
import os

delete = Blueprint('delete', __name__, url_prefix='/delete/', template_folder='templates')

BASEDIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.curdir)
load_dotenv(os.path.join(PARENT_DIR, '.env'))
db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
database_uri = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'


engine = create_engine(database_uri)

Session = sessionmaker(bind=engine)


@delete.route('/note/<uuid>/')
@requires_login
def delete_note(uuid):
    db_session = Session()

    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()
    db_session.delete(note)
    db_session.commit()
    flash(f'{note.title} deleted')
    return redirect(url_for('root'))


@delete.route('/flashcard/<uuid>/')
@requires_login
def delete_flashcard(uuid):
    db_session = Session()
    flashcard = db_session.query(Flashcard).join(Deck, Deck.id == Flashcard.deck_id)\
        .join(Collection, Deck.collection_id == Collection.id).join(User, Collection.user_id == User.id)\
        .filter(User.email == session['user']).filter(Collection.user_id == User.id)\
        .filter(Deck.collection_id == Collection.id).filter(Flashcard.deck_id == Deck.id)\
        .filter(Flashcard.uuid == uuid).first()

    deck = db_session.query(Deck).filter(Deck.id == flashcard.deck_id).first()
    db_session.delete(flashcard)
    db_session.commit()
    flash(f'{flashcard.title} deleted')
    return redirect(url_for('view.view_deck', uuid=deck.uuid))


@delete.route('/deck/<uuid>/')
@requires_login
def delete_deck(uuid):
    db_session = Session()
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Deck.uuid == uuid).first()
    try:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).delete()
    except:
        flashcards = None
    db_session.delete(deck)
    db_session.commit()
    flash(f'{deck.title} deleted')
    return redirect(url_for('root'))


@delete.route('/collection/<uuid>/')
@requires_login
def delete_collection(uuid):
    db_session = Session()
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()

    try:
        notes = db_session.query(Note).filter(Note.collection_id == collection.id).delete()
        db_session.commit()
    except:
        notes = None

    try:
        deck_items = db_session.query(Deck).filter(Deck.collection_id == collection.id).all()
        decks = db_session.query(Deck).filter(Deck.collection_id == collection.id).delete()

        for deck in deck_items:
            flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).delete()
            db_session.commit()
        db_session.commit()
    except:
        decks = None

    db_session.delete(collection)
    db_session.commit()

    flash(f'{collection.title} deleted')
    return redirect(url_for('root'))
