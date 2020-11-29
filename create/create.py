from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import User, Collection, Note, Flashcard, Deck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from authentication.auth import requires_login
import bleach
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os

# Register as blueprint
create = Blueprint('create', __name__, url_prefix='/create/', template_folder='templates')

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


# Flask decorator for creating a collection
@create.route('/collection/', methods=['GET', 'POST'])
@requires_login
def create_collection():
    # Create database session
    db_session = Session()
    if request.method == 'POST':
        try:
            # If the checkbox input is set, set public boolean true, otherwise set to false
            public_checkbox = request.form.get('public')
            if public_checkbox:
                public = True
            else:
                public = False
            # Sanitise title input, if it's empty, redirect to back to the page
            title = bleach.clean(request.form['title'])
            if not title:
                flash('Provide a title')
                return redirect(url_for('create.create_collection'))
            # Query the User table for the authenticated user
            user = db_session.query(User).filter(User.email == session['user']).first()
            # Query the Collection table to check if an existing collection with the same name exists
            collection_count = db_session.query(Collection).filter(Collection.title == title)\
                .filter(Collection.user_id == user.id).count()
            # If it exists, redirect back to the create collection page
            if collection_count >= 1:
                flash('Collection  already exists')
                return redirect(url_for('create.create_collection'))
            else:
                # Otherwise create a new collection and commit the changes, redirect back to root page
                # Create a uuid
                collection_uuid = str(uuid.uuid4())

                collection = Collection(user_id=user.id, uuid=collection_uuid, title=title, public=public)
                db_session.add(collection)
                db_session.commit()
                flash(f'Collection {title} created!')
                return redirect(url_for('root'))

        except IntegrityError:
            db_session.rollback()
            flash('Provide a title')
            return redirect(url_for('create.create_collection'))
        finally:
            # Close database session
            db_session.close()

    return render_template('create_collection.html')


# Flask decorator for creating a note
@create.route('/note/', methods=['GET', 'POST'])
@requires_login
def create_note():
    # Create database session
    db_session = Session()
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
            return redirect(url_for('create.create_note'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create.create_note'))
        if not data:
            flash('Note is empty')
            return redirect(url_for('create.create_note'))
        # Create a uuid
        note_uuid = str(uuid.uuid4())
        # Create a new note and commit it to the database
        note = Note(collection_id=collection, uuid=note_uuid, title=title, content=data, public=public,
                    edited=datetime.today())
        db_session.add(note)
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view.view_note', uuid=note_uuid))

    return render_template('create_note.html')


# Flask decorator for creating a deck
@create.route('/deck/', methods=['GET', 'POST'])
@requires_login
def create_deck():
    # Create database session
    db_session = Session()
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
            return redirect(url_for('create.create_deck'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create.create_deck'))
        # Create a uuid
        deck_uuid = str(uuid.uuid4())
        # Create deck
        deck = Deck(collection_id=collection, uuid=deck_uuid, title=title, public=public,
                    edited=datetime.today())
        db_session.add(deck)
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('create.create_flashcard'))
    return render_template('create_deck.html')


# Flask decorator for creating a flashcard
@create.route('/flashcard/', methods=['GET', 'POST'])
@requires_login
def create_flashcard():
    # Create database session
    db_session = Session()
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
            return redirect(url_for('create.create_flashcard'))
        if not deck:
            flash('Please choose a deck')
            return redirect(url_for('create.create_flashcard'))
        if not term:
            flash('Term is empty')
            return redirect(url_for('create.create_flashcard'))
        if not definition:
            flash('Definition is empty')
            return redirect(url_for('create.create_flashcard'))
        # Create flashcard
        flashcard = Flashcard(deck_id=deck, uuid=str(uuid.uuid4()), title=title, term=term, definition=definition,
                              edited=datetime.today())
        # modify the selected deck's edited timestamp
        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()
        selected_deck.edited = datetime.today()
        db_session.add(flashcard)
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view.view_deck', uuid=selected_deck.uuid))
    try:
        # Return all decks that belong to the user
        decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
            .join(User, Collection.user_id == User.id).filter(User.email == session['user']).all()
    except:
        decks = None
    return render_template('create_flashcard.html', decks=decks)
