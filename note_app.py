from flask import Flask, request, render_template, redirect, url_for, flash, session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User, Collection, Note, Flashcard, Deck
import uuid
from authentication.auth import authentication, requires_login
from datetime import datetime
import bleach


app = Flask(__name__, static_folder="static")
app.secret_key = 'A0Zr98j/3yXR~XHH!jmN]LWX/,?RT'
app.register_blueprint(authentication)
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False})

Session = sessionmaker(bind=engine)
db_session = Session()

allowed_tags = ['div', 'table', 'tr', 'td', 'tbody', 'br', 'p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
attrs = {'*': ['*']}


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

    decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .order_by(desc('edited')).limit(3).all()

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


@app.route('/sh/collection/<uuid>/')
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


@app.route('/sh/note/<uuid>/')
def view_public_note(uuid):
    note = db_session.query(Note).filter(Note.public == True).filter(Note.uuid == uuid).first()
    return render_template('view_note.html', note=note)


@app.route('/sh/deck/<uuid>/')
def view_public_deck(uuid):
    deck = db_session.query(Deck).filter(Deck.public == True).filter(Deck.uuid == uuid).first()
    try:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        flashcards = None
    return render_template('view_deck.html', deck=deck, flashcards=flashcards)


@app.route('/collection/<uuid>/')
@requires_login
def view_collection(uuid):

    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()

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

    return render_template('view_collection.html', collection=collection, notes=notes, decks=decks_list)


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
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
        .filter(Deck.uuid == uuid).first()
    try:
        flashcards = db_session.query(Flashcard).filter(Flashcard.deck_id == deck.id).all()
    except:
        flashcards = None
    return render_template('view_deck.html', deck=deck, flashcards=flashcards)


@app.route('/create/collection/', methods=['GET', 'POST'])
@requires_login
def create_collection():
    if request.method == 'POST':
        try:
            public_checkbox = request.form.get('public')
            if public_checkbox:
                public = True
            else:
                public = False
            title = bleach.clean(request.form['title'])
            if not title:
                flash('Provide a title')
                return redirect(url_for('create_collection'))

            collection_count = db_session.query(Collection).filter(Collection.title == title).count()
            if collection_count >= 1:
                flash('Collection  already exists')
                return redirect(url_for('create_collection'))
            else:
                user = db_session.query(User).filter(User.email == session['user']).first()

                collection_uuid = str(uuid.uuid4())

                collection = Collection(user_id=user.id, uuid=collection_uuid, title=title, public=public)
                db_session.add(collection)
                db_session.commit()
                flash(f'Collection {title} created!')
                return redirect(url_for('root'))

        except IntegrityError:
            flash('Provide a title')
            return redirect(url_for('create_collection'))

    return render_template('create_collection.html')


@app.route('/create/note/', methods=['GET', 'POST'])
@requires_login
def create_note():
    if request.method == 'POST':
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False

        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])
        data = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                            attributes=attrs, styles=['*'])
        if not title:
            flash('Please include title')
            return redirect(url_for('create_note'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create_note'))
        if not data:
            flash('Note is empty')
            return redirect(url_for('create_note'))

        note_uuid = str(uuid.uuid4())

        note = Note(collection_id=collection, uuid=note_uuid, title=title, content=data, public=public,
                    edited=datetime.today())
        db_session.add(note)
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view_note', uuid=note_uuid))
    return render_template('create_note.html')


@app.route('/create/deck/', methods=['GET', 'POST'])
@requires_login
def create_deck():
    if request.method == 'POST':
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False
        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])
        if not title:
            flash('Please include title')
            return redirect(url_for('create_deck'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create_deck'))

        deck_uuid = str(uuid.uuid4())

        deck = Deck(collection_id=collection, uuid=deck_uuid, title=title, public=public,
                    edited=datetime.today())
        db_session.add(deck)
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('view_deck', uuid=deck_uuid))
    return render_template('create_deck.html')


@app.route('/create/flashcard/', methods=['GET', 'POST'])
@requires_login
def create_flashcard():
    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        deck = bleach.clean(request.form['deck'])
        term = bleach.clean(request.form['term'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                            attributes=attrs, styles=['background-colour'])
        definition = bleach.clean(request.form['definition'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                                  attributes=attrs, styles=['background-colour'])
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

        flashcard = Flashcard(deck_id=deck, uuid=str(uuid.uuid4()), title=title, term=term, definition=definition,
                              edited=datetime.today())

        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()
        selected_deck.edited = datetime.today()
        db_session.add(flashcard)
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view_deck', uuid=selected_deck.uuid))
    try:
        decks = db_session.query(Deck).all()
    except:
        decks = None
    return render_template('create_flashcard.html', decks=decks)


@app.route('/edit/collection/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_collection(uuid):
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()

    edit = True
    if request.method == 'POST':
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False

        title = bleach.clean(request.form['title'])

        if not title:
            flash('Please include title')
            return redirect(url_for('edit_collection', uuid=collection.uuid))

        collection.title = title
        collection.public = public
        db_session.commit()
        flash('Collection Saved!')
        return redirect(url_for('view_collection', uuid=collection.uuid))

    return render_template('create_collection.html', edit=edit, collection=collection)


@app.route('/edit/note/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_note(uuid):
    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()
    edit = True
    if request.method == 'POST':
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False

        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])
        data = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                            attributes=attrs, styles=['background-colour'])
        if not title:
            flash('Please include title')
            return redirect(url_for('edit_note', uuid=note.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit_note', uuid=note.uuid))
        if not data:
            flash('Note is empty')
            return redirect(url_for('edit_note', uuid=note.uuid))

        note.title = title
        note.collection_id = collection
        note.content = data
        note.public = public
        note.edited = datetime.today()
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view_note', uuid=note.uuid))

    return render_template('create_note.html', edit=edit, note=note)


@app.route('/edit/deck/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_deck(uuid):
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
        .filter(Deck.uuid == uuid).first()
    edit = True
    if request.method == 'POST':
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False

        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])

        if not title:
            flash('Please include title')
            return redirect(url_for('edit_deck', uuid=deck.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit_deck', uuid=deck.uuid))

        deck.title = title
        deck.collection_id = collection
        deck.public = public
        deck.edited = datetime.today()
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('view_deck', uuid=deck.uuid))

    return render_template('create_deck.html', edit=edit, deck=deck)


@app.route('/edit/flashcard/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_flashcard(uuid):
    flashcard = db_session.query(Flashcard).join(Deck, Flashcard.deck_id == Deck.id)\
        .join(Collection, Deck.collection_id == Collection.id).join(User, Collection.user_id == User.id)\
        .filter(User.email == session['user']).filter(Collection.user_id == User.id)\
        .filter(Deck.collection_id == Collection.id) .filter(Flashcard.uuid == uuid).first()

    edit = True

    try:
        decks = db_session.query(Deck).all()
    except:
        decks = None

    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        deck = bleach.clean(request.form['deck'])
        term = bleach.clean(request.form['term'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                            attributes=attrs, styles=['background-colour'])
        definition = bleach.clean(request.form['definition'], tags=bleach.sanitizer.ALLOWED_TAGS + allowed_tags,
                                  attributes=attrs, styles=['background-colour'])

        if not title:
            flash('Please include title')
            return redirect(url_for('edit_flashcard', uuid=flashcard.uuid))
        if not deck:
            flash('Please choose a deck')
            return redirect(url_for('edit_flashcard', uuid=flashcard.uuid))
        if not term:
            flash('Term is empty')
            return redirect(url_for('edit_flashcard', uuid=flashcard.uuid))
        if not definition:
            flash('Definition is empty')
            return redirect(url_for('edit_flashcard', uuid=flashcard.uuid))

        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()

        flashcard.title = title
        flashcard.deck_id = deck
        flashcard.term = term
        flashcard.definition = definition
        flashcard.edited = datetime.today()
        selected_deck.edited = datetime.today()
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view_deck', uuid=selected_deck.uuid))

    return render_template('create_flashcard.html', edit=edit, flashcard=flashcard, decks=decks)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
