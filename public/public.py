from flask import Blueprint, render_template
from models import Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Register as blueprint
public = Blueprint('public', __name__, url_prefix='/public/', template_folder='templates')

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


# Flask decorator for viewing a public collection
@public.route('/collection/<uuid>/')
def view_public_collection(uuid):
    # Create database session
    db_session = Session()
    # Query the database for the collection, filter by uuid and check if it's public
    collection = db_session.query(Collection).filter(Collection.public == True)\
        .filter(Collection.uuid == uuid).first()
    try:
        # Join Note and Collection table
        # Query all notes that belong to the collection and check if they are public
        notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id)\
            .filter(Note.public == True).filter(Note.collection_id == collection.id).all()
    except:
        notes = None

    try:
        decks_list = []
        # Join Deck and Collection table
        # Query all decks that belong to the collection and check if they are public
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .filter(Deck.public == True).filter(Deck.collection_id == collection.id).all()
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

    return render_template('view_collection.html', collection=collection, notes=notes, decks=decks_list)


# Flask decorator for viewing a public note
@public.route('/note/<uuid>/')
def view_public_note(uuid):
    # Create database session
    db_session = Session()
    # Query the database for the note, filter by uuid and check if it's public
    note = db_session.query(Note).filter(Note.public == True).filter(Note.uuid == uuid).first()
    return render_template('view_note.html', note=note)


# Flask decorator for viewing a public deck
@public.route('/deck/<uuid>/')
def view_public_deck(uuid):
    # Create database session
    db_session = Session()
    # Query the database for the deck, filter by uuid and check if it's public
    deck = db_session.query(Deck).filter(Deck.public == True).filter(Deck.uuid == uuid).first()
    try:
        # Get all flashcards that belong to the deck
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        flashcards = None
    return render_template('view_deck.html', deck=deck, flashcards=flashcards)
