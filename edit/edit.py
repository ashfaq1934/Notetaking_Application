from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from authentication.auth import requires_login
import bleach
from datetime import datetime
from dotenv import load_dotenv
import os

edit = Blueprint('edit', __name__, url_prefix='/edit/', template_folder='templates')

BASEDIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.curdir)
load_dotenv(os.path.join(PARENT_DIR, '.env'))
db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
database_uri = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'


engine = create_engine(database_uri)
print(BASEDIR)
print(PARENT_DIR)
print(database_uri)
print('-------------------------------------------------')

Session = sessionmaker(bind=engine)

allowed_tags = ['a', 'abbr', 'acronym', 'blockquote', 'address', 'b', 'br', 'div', 'dl', 'dt',
                'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                'li', 'ol', 'p', 'pre', 'q', 's', 'em', 'small', 'strike', 'strong',
                'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                'thead', 'tr', 'tt', 'u', 'ul']

allowed_styles = [
    'color', 'background-color', 'font', 'font-weight',
    'height', 'max-height', 'min-height',
    'width', 'max-width', 'min-width']


allowed_attributes = {
    '*': ['class', 'title', 'style'],
    'a': ['href', 'rel'],
    'img': ['alt', 'src', 'width', 'height', 'align', 'style']
}


@edit.route('/collection/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_collection(uuid):
    db_session = Session()
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
            return redirect(url_for('edit.edit_collection', uuid=collection.uuid))

        collection.title = title
        collection.public = public
        db_session.commit()
        flash('Collection Saved!')
        return redirect(url_for('view.view_collection', uuid=collection.uuid))

    return render_template('create_collection.html', edit=edit, collection=collection)


@edit.route('/note/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_note(uuid):
    db_session = Session()
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
        data = bleach.clean(request.form['editordata'], tags=allowed_tags, attributes=allowed_attributes,
                            styles=allowed_styles, protocols=['data'], strip=True)
        if not title:
            flash('Please include title')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))
        if not data:
            flash('Note is empty')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))

        note.title = title
        note.collection_id = collection
        note.content = data
        note.public = public
        note.edited = datetime.today()
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view.view_note', uuid=note.uuid))

    return render_template('create_note.html', edit=edit, note=note)


@edit.route('/deck/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_deck(uuid):
    db_session = Session()
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
            return redirect(url_for('edit.edit_deck', uuid=deck.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit.edit_deck', uuid=deck.uuid))

        deck.title = title
        deck.collection_id = collection
        deck.public = public
        deck.edited = datetime.today()
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('view.view_deck', uuid=deck.uuid))

    return render_template('create_deck.html', edit=edit, deck=deck)


@edit.route('/flashcard/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_flashcard(uuid):
    db_session = Session()
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
        term = bleach.clean(request.form['term'], tags=allowed_tags, attributes=allowed_attributes,
                            styles=allowed_styles, protocols=['data'], strip=True)
        definition = bleach.clean(request.form['definition'], tags=allowed_tags, attributes=allowed_attributes,
                                  styles=allowed_styles, protocols=['data'], strip=True)

        if not title:
            flash('Please include title')
            return redirect(url_for('edit.edit_flashcard', uuid=flashcard.uuid))
        if not deck:
            flash('Please choose a deck')
            return redirect(url_for('edit.edit_flashcard', uuid=flashcard.uuid))
        if not term:
            flash('Term is empty')
            return redirect(url_for('edit.edit_flashcard', uuid=flashcard.uuid))
        if not definition:
            flash('Definition is empty')
            return redirect(url_for('edit.edit_flashcard', uuid=flashcard.uuid))

        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()

        flashcard.title = title
        flashcard.deck_id = deck
        flashcard.term = term
        flashcard.definition = definition
        flashcard.edited = datetime.today()
        selected_deck.edited = datetime.today()
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view.view_deck', uuid=selected_deck.uuid, edit=edit, decks=decks))
    return render_template('create_flashcard.html', edit=edit, flashcard=flashcard, decks=decks)
