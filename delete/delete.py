from flask import Blueprint, redirect, url_for, flash, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from authentication.auth import requires_login
from dotenv import load_dotenv
import os

# Register as blueprint
delete = Blueprint('delete', __name__, url_prefix='/delete/', template_folder='templates')

# Load parent directory of application and load the .env file
PARENT_DIR = os.path.abspath(os.curdir)
load_dotenv(os.path.join(PARENT_DIR, '.env'))

# Get data configuration settings and create the database URI
db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
database_uri = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'

# Connect to the database
engine = create_engine(database_uri)

# Bind session maker to engine
Session = sessionmaker(bind=engine)

# Flask decorator for deleting a note
@delete.route('/note/<uuid>/')
@requires_login
def delete_note(uuid):
    # Create database session
    db_session = Session()
    # Join Note, User and Collection table to check which user is authenticated
    # Query database for the note, filter by uuid
    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()
    db_session.delete(note)
    db_session.commit()
    flash(f'{note.title} deleted')
    return redirect(url_for('root'))


# Flask decorator for deleting a flashcard
@delete.route('/flashcard/<uuid>/')
@requires_login
def delete_flashcard(uuid):
    # Create database session
    db_session = Session()
    # Join Collection, User, Deck and Flashcard table to check which user is authenticated
    # Query database for the flashcard, filter by uuid
    flashcard = db_session.query(Flashcard).join(Deck, Deck.id == Flashcard.deck_id)\
        .join(Collection, Deck.collection_id == Collection.id).join(User, Collection.user_id == User.id)\
        .filter(User.email == session['user']).filter(Collection.user_id == User.id)\
        .filter(Deck.collection_id == Collection.id).filter(Flashcard.deck_id == Deck.id)\
        .filter(Flashcard.uuid == uuid).first()
    # Get the flashcard's deck and redirect to it after deleting the flashcard
    deck = db_session.query(Deck).filter(Deck.id == flashcard.deck_id).first()
    db_session.delete(flashcard)
    db_session.commit()
    flash(f'{flashcard.title} deleted')
    return redirect(url_for('view.view_deck', uuid=deck.uuid))


# Flask decorator for deleting a deck
@delete.route('/deck/<uuid>/')
@requires_login
def delete_deck(uuid):
    # Create database session
    db_session = Session()
    # Join Collection, User and Deck table to check which user is authenticated
    # Query database for the deck, filter by uuid
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Deck.uuid == uuid).first()
    try:
        # Delete all flashcards that belong to the deck
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).delete()
    except:
        flashcards = None
    # Delete deck
    db_session.delete(deck)
    db_session.commit()
    flash(f'{deck.title} deleted')
    return redirect(url_for('root'))


# Flask decorator for deleting a collection
@delete.route('/collection/<uuid>/')
@requires_login
def delete_collection(uuid):
    # Create database session
    db_session = Session()
    # Join User and Collection table to check which user is authenticated
    # Query the database for the collection, filter by uuid
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()

    try:
        # Delete all notes that belong to the collection
        notes = db_session.query(Note).filter(Note.collection_id == collection.id).delete()
        db_session.commit()
    except:
        notes = None

    try:
        # Get all decks that belong to the collection
        deck_items = db_session.query(Deck).filter(Deck.collection_id == collection.id).all()
        # Delete all the decks that belong to the collection
        decks = db_session.query(Deck).filter(Deck.collection_id == collection.id).delete()
        # Get all flashcards that belong to the deck and delete them
        for deck in deck_items:
            flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).delete()
            db_session.commit()
        db_session.commit()
    except:
        decks = None
    # Finally delete the collection after all it's referenced resources have been deleted
    db_session.delete(collection)
    db_session.commit()

    flash(f'{collection.title} deleted')
    return redirect(url_for('root'))
