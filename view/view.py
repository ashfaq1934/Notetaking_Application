from flask import Blueprint, render_template, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from authentication.auth import requires_login


view = Blueprint('view', __name__, url_prefix='/view/', template_folder='templates')
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False}, echo=True)

Session = sessionmaker(bind=engine)
db_session = Session()


@view.route('/collection/<uuid>/')
@requires_login
def view_collection(uuid):

    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()

    view = True

    try:
        notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Note.collection_id == collection.id).all()
    except:
        notes = None

    try:
        decks_list = []
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == collection.id).all()

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

    return render_template('view_collection.html', collection=collection, notes=notes, decks=decks_list, view=view)


@view.route('/note/<uuid>/')
@requires_login
def view_note(uuid):
    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()

    note_collection = db_session.query(Collection).filter(Collection.id == note.collection_id).first()

    view = True

    return render_template('view_note.html', note=note, view=view, note_collection=note_collection)


@view.route('/deck/<uuid>/')
@requires_login
def view_deck(uuid):
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
        .filter(Deck.uuid == uuid).first()

    deck_collection = db_session.query(Collection).filter(Collection.id == deck.collection_id).first()

    view = True

    try:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        flashcards = None

    return render_template('view_deck.html', deck=deck, flashcards=flashcards, view=view,
                           deck_collection=deck_collection)
