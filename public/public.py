from flask import Blueprint, render_template
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


public = Blueprint('public', __name__, url_prefix='/public/', template_folder='templates')
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False}, echo=True)

Session = sessionmaker(bind=engine)
db_session = Session()


@public.route('/collection/<uuid>/')
def view_public_collection(uuid):
    collection = db_session.query(Collection).filter(Collection.public == True)\
        .filter(Collection.uuid == uuid).first()
    try:
        notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id)\
            .filter(Note.public == True).filter(Note.collection_id == collection.id).all()
    except:
        notes = None

    try:
        decks_list = []
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .filter(Deck.public == True).filter(Deck.collection_id == collection.id).all()

        for deck in decks:
            decks_list.append(deck.__dict__)

        for deck in decks_list:
            flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck['id']).all()
            flashcards_list = []
            for flashcard in flashcards:
                flashcards_list.append(flashcard.__dict__)

            deck['flashcards'] = flashcards_list
    except:
        decks_list = None

    return render_template('view_collection.html', collection=collection, notes=notes, decks=decks_list)


@public.route('/note/<uuid>/')
def view_public_note(uuid):
    note = db_session.query(Note).filter(Note.public == True).filter(Note.uuid == uuid).first()
    return render_template('view_note.html', note=note)


@public.route('/deck/<uuid>/')
def view_public_deck(uuid):
    deck = db_session.query(Deck).filter(Deck.public == True).filter(Deck.uuid == uuid).first()
    try:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        flashcards = None
    return render_template('view_deck.html', deck=deck, flashcards=flashcards)
