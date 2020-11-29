from flask import Blueprint, render_template, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from authentication.auth import requires_login
from dotenv import load_dotenv
import os

# Register as blueprint
view = Blueprint('view', __name__, url_prefix='/view/', template_folder='templates')

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
Session = sessionmaker(bind=engine, autoflush=True)


# Flask decorator for viewing a collection
@view.route('/collection/<uuid>/')
@requires_login
def view_collection(uuid):
    # Create database session
    db_session = Session()
    # Join User and Collection table to check which user is authenticated
    # Query the database for the collection, filter by uuid
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()
    # Boolean for authenticated users, would be used in the template
    view = True

    try:
        # Join User, Note and Collection table to check which user is authenticated
        # Query all notes that belong to the collection
        notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Note.collection_id == collection.id).all()
    except:
        notes = None

    try:
        decks_list = []
        # Join User, Deck and Collection table to check which user is authenticated
        # Query all decks that belong to the collection
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == collection.id).all()
        # append decks to the empty list as python dictionaries so that they can be modified
        # This also makes it easier to work with in the template
        for deck in decks:
            decks_list.append(deck.__dict__)

        for deck in decks_list:
            # Get all flashcards that belong to each deck in the list of decks
            flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck['id']).all()
            flashcards_list = []
            for flashcard in flashcards:
                flashcards_list.append(flashcard.__dict__)
            # Append the list of flashcards for each deck to the the deck dictionary as a sub array
            deck['flashcards'] = flashcards_list
    except:
        decks_list = None
        db_session.rollback()
    finally:
        # Close session
        db_session.close()

    return render_template('view_collection.html', collection=collection, notes=notes, decks=decks_list, view=view)


# Flask decorator for viewing a note
@view.route('/note/<uuid>/')
@requires_login
def view_note(uuid):
    # Create database session
    db_session = Session()
    try:
        # Join User, Note and Collection table to check which user is authenticated
        # Query the database for the note, filter by uuid
        note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
            .filter(Note.uuid == uuid).first()
        # Get the note's collection
        note_collection = db_session.query(Collection).filter(Collection.id == note.collection_id).first()
        # Boolean for authenticated users, would be used in the template
        view = True
    except:
        note = None
        note_collection = None
        view = None
        db_session.rollback()
    finally:
        db_session.close()

    return render_template('view_note.html', note=note, view=view, note_collection=note_collection)


# Flask decorator for viewing a deck
@view.route('/deck/<uuid>/')
@requires_login
def view_deck(uuid):
    # Create database session
    db_session = Session()
    try:
        # Join User, Deck and Collection table to check which user is authenticated
        # Query the database for the deck, filter by uuid
        deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
            .filter(Deck.uuid == uuid).first()
        # Get the deck's collection
        deck_collection = db_session.query(Collection).filter(Collection.id == deck.collection_id).first()
        # Boolean for authenticated users, would be used in the template
        view = True

        try:
            # Get all flashcards that belong to the deck
            flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
        except:
            flashcards = None
            db_session.rollback()
    except:
        deck = None
        deck_collection = None
        view = None
        flashcards = None
        db_session.rollback()
    finally:
        db_session.close()

    return render_template('view_deck.html', deck=deck, flashcards=flashcards, view=view,
                           deck_collection=deck_collection)
