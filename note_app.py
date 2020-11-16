from flask import Flask, request, render_template, redirect, url_for, flash, session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User, Collection, Note, Flashcard, Deck
from authentication.auth import authentication, requires_login
from view.view import view
from public.public import public
from create.create import create
from edit.edit import edit
from delete.delete import delete


app = Flask(__name__, static_folder="static")
app.secret_key = 'A0Zr98j/3yXR~XHH!jmN]LWX/,?RT'
app.register_blueprint(authentication)
app.register_blueprint(view)
app.register_blueprint(public)
app.register_blueprint(create)
app.register_blueprint(edit)
app.register_blueprint(delete)
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False})

Session = sessionmaker(bind=engine)
db_session = Session()


@app.context_processor
def get_collections():
    try:
        collections = db_session.query(Collection).join(User, Collection.user_id == User.id) \
            .filter(User.email == session['user']).all()
        return dict(collections=collections)
    except:
        return dict(collections=None)


@app.context_processor
def resources_processor():
    def get_resources(id):
        notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Note.collection_id == id).all()

        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == id).all()

        return notes, decks

    return dict(get_resources=get_resources)


@app.route('/', methods=['GET'])
@requires_login
def root():
    notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user'])\
        .order_by(desc('edited')).limit(3).all()

    decks_list = []
    decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .order_by(desc('edited')).limit(3).all()

    for deck in decks:
        decks_list.append(deck.__dict__)

    for deck in decks_list:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck['id']).all()
        flashcards_list = []
        for flashcard in flashcards:
            flashcards_list.append(flashcard.__dict__)
        deck['flashcards'] = flashcards_list

    return render_template('main.html', notes=notes, decks=decks)


@app.route('/browse/', methods=['GET'])
def browse():
    recent_notes = db_session.query(Note).filter(Note.public == True).order_by(desc('edited')).limit(3).all()
    recent_decks = db_session.query(Deck).filter(Note.public == True).order_by(desc('edited')).limit(3).all()
    query = request.args.get('query')
    if query:
        search = "%{}%".format(query)
        searched_notes = db_session.query(Note).filter(Note.title.like(search)).all()
        searched_decks = db_session.query(Deck).filter(Deck.public == True).filter(Deck.title.like(search)).all()
        searched_collections = db_session.query(Deck).filter(Collection.public == True)\
            .filter(Collection.title.like(search)).all()
        print(searched_notes)

    else:
        searched_notes = None
        searched_decks = None
        searched_collections = None
    return render_template('browse.html', recent_notes=recent_notes, recent_decks=recent_decks, searched_notes=searched_notes,
                           searched_decks=searched_decks, searched_collections=searched_collections)


@app.route('/search/', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        search_query = "%{}%".format(query)
        searched_notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Note.title.like(search_query)).all()

        searched_decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.title.like(search_query)).all()

        searched_collections = db_session.query(Collection).join(User, Collection.user_id == User.id) \
            .filter(User.email == session['user']).filter(Collection.title.like(search_query)).all()
    else:
        searched_notes = None
        searched_decks = None
        searched_collections = None

    return render_template('search_results.html', searched_collections=searched_collections,
                           searched_notes=searched_notes, searched_decks=searched_decks)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
