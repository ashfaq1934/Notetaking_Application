from flask import Flask, request, render_template, redirect, url_for, flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User, Collection, Note, Flashcard, Deck
import uuid
from authentication.auth import authentication, requires_login
from datetime import datetime

app = Flask(__name__, static_folder="static")
app.secret_key = 'A0Zr98j/3yXR~XHH!jmN]LWX/,?RT'
app.register_blueprint(authentication)
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False})

Session = sessionmaker(bind=engine)
db_session = Session()


# Todo: implement input sanitization


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

        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id)\
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == id).all()

        return notes, decks

    return dict(get_resources=get_resources)


@app.route('/', methods=['GET'])
def root():
    if session.get('logged_in'):
        return render_template('main.html')
    return redirect(url_for('auth.login'))


@app.route('/collection/<uuid>/')
@requires_login
def view_collection(uuid):
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()
    return render_template('view_collection.html', collection=collection)


@app.route('/note/<uuid>/')
@requires_login
def view_note(uuid):
    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()
    return render_template('view_note.html', note=note)


@app.route('/deck/<uuid>/')
@requires_login
def view_deck(uuid):
    try:
        deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
            .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
            .filter(Deck.uuid == uuid).first()
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        deck = None
        flashcards = None
    return render_template('view_deck.html', deck=deck, flashcards=flashcards)


@app.route('/create/collection/', methods=['GET', 'POST'])
@requires_login
def create_collection():
    if request.method == 'POST':
        try:
            title = request.form['title']
            if not title:
                flash('Provide a title')
                return redirect(url_for('create_collection'))

            collection_count = db_session.query(Collection).filter(Collection.title == title).count()
            if collection_count >= 1:
                flash('Collection  already exists')
                return redirect(url_for('create_collection'))
            else:
                user = db_session.query(User).filter(User.email == session['user']).first()
                collection = Collection(user_id=user.id, uuid=str(uuid.uuid4()), title=title, public=False)
                db_session.add(collection)
                db_session.commit()
                flash(f'Collection {title} created!')
                return redirect(url_for('root'))

        except IntegrityError:
            flash('Provide a title')
            return redirect(url_for('create_collection'))

    return render_template('create_collection.html')


@app.route('/create/note/', methods=['GET', 'POST'])
def create_note():
    if request.method == 'POST':
        title = request.form['title']
        collection = request.form['collection']
        data = request.form['editordata']
        if not title:
            flash('Please include title')
            return redirect(url_for('create_note'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create_note'))
        if not data:
            flash('Note is empty')
            return redirect(url_for('create_note'))

        note = Note(collection_id=collection, uuid=str(uuid.uuid4()), title=title, content=data, public=False,
                    edited=datetime.today())
        db_session.add(note)
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('root'))
    return render_template('create_note.html')


@app.route('/create/deck/', methods=['GET', 'POST'])
def create_deck():
    if request.method == 'POST':
        title = request.form['title']
        collection = request.form['collection']
        if not title:
            flash('Please include title')
            return redirect(url_for('create_deck'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create_deck'))

        deck = Deck(collection_id=collection, uuid=str(uuid.uuid4()), title=title, public=False,
                    edited=datetime.today())
        db_session.add(deck)
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('root'))
    return render_template('create_deck.html')


@app.route('/create/flashcard/', methods=['GET', 'POST'])
def create_flashcard():
    if request.method == 'POST':
        title = request.form['title']
        deck = request.form['deck']
        term = request.form['term']
        definition = request.form['definition']
        if not title:
            flash('Please include title')
            return redirect(url_for('create_flashcard'))
        if not deck:
            flash('Please choose a deck')
            return redirect(url_for('create_flashcard'))
        if not term:
            flash('Term is empty')
            return redirect(url_for('create_flashcard'))
        if not definition:
            flash('Definition is empty')
            return redirect(url_for('create_flashcard'))

        flashcard = Flashcard(deck_id=deck, uuid=str(uuid.uuid4()), title=title, term=term,
                              definition=definition, public=False, edited=datetime.today())
        db_session.add(flashcard)
        db_session.commit()
        flash('Flashcard Saved!')
        return redirect(url_for('root'))
    try:
        decks = db_session.query(Deck).all()
    except:
        decks = None
    return render_template('create_flashcard.html', decks=decks)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
