from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from authentication.auth import requires_login
import bleach
from datetime import datetime
from dotenv import load_dotenv
import os

# Register as blueprint
edit = Blueprint('edit', __name__, url_prefix='/edit/', template_folder='templates')

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

# List of allowed HTML tags
allowed_tags = ['a', 'abbr', 'acronym', 'blockquote', 'address', 'b', 'br', 'div', 'dl', 'dt',
                'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                'li', 'ol', 'p', 'pre', 'q', 's', 'em', 'small', 'strike', 'strong',
                'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                'thead', 'tr', 'tt', 'u', 'ul']

# List of allowed CSS styles
allowed_styles = [
    'color', 'background-color', 'font', 'font-weight',
    'height', 'max-height', 'min-height',
    'width', 'max-width', 'min-width']

# List of allowed attributes
allowed_attributes = {
    '*': ['class', 'title', 'style'],
    'a': ['href', 'rel'],
    'img': ['alt', 'src', 'width', 'height', 'align', 'style']
}


# Flask decorator for editing a collection
@edit.route('/collection/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_collection(uuid):
    # Create database session
    db_session = Session()
    collection = db_session.query(Collection).join(User, Collection.user_id == User.id) \
        .filter(User.email == session['user']).filter(Collection.uuid == uuid).first()
    # boolean to be used on the template when user is in edit view
    edit = True
    if request.method == 'POST':
        # If the checkbox input is set, set public boolean true, otherwise set to false
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False
        # Sanitise inputs
        title = bleach.clean(request.form['title'])
        # If inputs are empty, redirect back to page
        if not title:
            flash('Please include title')
            return redirect(url_for('edit.edit_collection', uuid=collection.uuid))
        # Modify collection
        collection.title = title
        collection.public = public
        db_session.commit()
        flash('Collection Saved!')
        return redirect(url_for('view.view_collection', uuid=collection.uuid))

    return render_template('create_collection.html', edit=edit, collection=collection)


# Flask decorator for editing a note
@edit.route('/note/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_note(uuid):
    # Create database session
    db_session = Session()
    note = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Note.collection_id == Collection.id) \
        .filter(Note.uuid == uuid).first()
    # boolean to be used on the template when user is in edit view
    edit = True
    if request.method == 'POST':
        # If the checkbox input is set, set public boolean true, otherwise set to false
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False
        # Sanitise inputs
        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])
        # Pass bleach the lists of allowed HTML tags, attributes and styles so that it doesn't remove them
        # Pass in data protocol so that images can be uploaded
        # Strip anything away that hasn't been whitelisted
        data = bleach.clean(request.form['editordata'], tags=allowed_tags, attributes=allowed_attributes,
                            styles=allowed_styles, protocols=['data'], strip=True)
        # If inputs are empty, redirect back to page
        if not title:
            flash('Please include title')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))
        if not data:
            flash('Note is empty')
            return redirect(url_for('edit.edit_note', uuid=note.uuid))
        # Modify note
        note.title = title
        note.collection_id = collection
        note.content = data
        note.public = public
        note.edited = datetime.today()
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view.view_note', uuid=note.uuid))

    return render_template('create_note.html', edit=edit, note=note)


# Flask decorator for editing a deck
@edit.route('/deck/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_deck(uuid):
    # Create database session
    db_session = Session()
    deck = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .filter(Collection.user_id == User.id).filter(Deck.collection_id == Collection.id) \
        .filter(Deck.uuid == uuid).first()
    # boolean to be used on the template when user is in edit view
    edit = True
    if request.method == 'POST':
        # If the checkbox input is set, set public boolean true, otherwise set to false
        public_checkbox = request.form.get('public')
        if public_checkbox:
            public = True
        else:
            public = False
        # Sanitise inputs
        title = bleach.clean(request.form['title'])
        collection = bleach.clean(request.form['collection'])
        # If inputs are empty, redirect back to page
        if not title:
            flash('Please include title')
            return redirect(url_for('edit.edit_deck', uuid=deck.uuid))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('edit.edit_deck', uuid=deck.uuid))
        # Modify deck
        deck.title = title
        deck.collection_id = collection
        deck.public = public
        deck.edited = datetime.today()
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('view.view_deck', uuid=deck.uuid))

    return render_template('create_deck.html', edit=edit, deck=deck)


# Flask decorator for editing a flashcard
@edit.route('/flashcard/<uuid>/', methods=['GET', 'POST'])
@requires_login
def edit_flashcard(uuid):
    # Create database session
    db_session = Session()
    flashcard = db_session.query(Flashcard).join(Deck, Flashcard.deck_id == Deck.id)\
        .join(Collection, Deck.collection_id == Collection.id).join(User, Collection.user_id == User.id)\
        .filter(User.email == session['user']).filter(Collection.user_id == User.id)\
        .filter(Deck.collection_id == Collection.id) .filter(Flashcard.uuid == uuid).first()
    # boolean to be used on the template when user is in edit view
    edit = True
    try:
        # Return all decks that belong to the use
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']).all()
    except:
        decks = None

    if request.method == 'POST':
        # Sanitise inputs
        title = bleach.clean(request.form['title'])
        deck = bleach.clean(request.form['deck'])
        # Pass bleach the lists of allowed HTML tags, attributes and styles so that it doesn't remove them
        # Pass in data protocol so that images can be uploaded
        # Strip anything away that hasn't been whitelisted
        term = bleach.clean(request.form['term'], tags=allowed_tags, attributes=allowed_attributes,
                            styles=allowed_styles, protocols=['data'], strip=True)
        definition = bleach.clean(request.form['definition'], tags=allowed_tags, attributes=allowed_attributes,
                                  styles=allowed_styles, protocols=['data'], strip=True)
        # If inputs are empty, redirect back to page
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
        # Get selected deck
        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()
        # Modify deck
        flashcard.title = title
        flashcard.deck_id = deck
        flashcard.term = term
        flashcard.definition = definition
        flashcard.edited = datetime.today()
        # Update selected deck's edited timestamp
        selected_deck.edited = datetime.today()
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view.view_deck', uuid=selected_deck.uuid, edit=edit, decks=decks))
    return render_template('create_flashcard.html', edit=edit, flashcard=flashcard, decks=decks)
