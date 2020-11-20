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

load_dotenv()

create = Blueprint('create', __name__, url_prefix='/create/', template_folder='templates')

db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
db_port = os.getenv("DATABASE_PORT")
engine = create_engine('mysql+pymysql://' + db_user + ':' + db_password + '@' + db_host + '/' + db_name)

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


@create.route('/collection/', methods=['GET', 'POST'])
@requires_login
def create_collection():
    db_session = Session()
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
                return redirect(url_for('create.create_collection'))

            collection_count = db_session.query(Collection).filter(Collection.title == title).count()
            if collection_count >= 1:
                flash('Collection  already exists')
                return redirect(url_for('create.create_collection'))
            else:
                user = db_session.query(User).filter(User.email == session['user']).first()

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
            db_session.close()

    return render_template('create_collection.html')


@create.route('/note/', methods=['GET', 'POST'])
@requires_login
def create_note():
    db_session = Session()
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
            return redirect(url_for('create.create_note'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create.create_note'))
        if not data:
            flash('Note is empty')
            return redirect(url_for('create.create_note'))

        note_uuid = str(uuid.uuid4())

        note = Note(collection_id=collection, uuid=note_uuid, title=title, content=data, public=public,
                    edited=datetime.today())
        db_session.add(note)
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('view.view_note', uuid=note_uuid))

    return render_template('create_note.html')


@create.route('/deck/', methods=['GET', 'POST'])
@requires_login
def create_deck():
    db_session = Session()
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
            return redirect(url_for('create.create_deck'))
        if not collection:
            flash('Please choose a collection')
            return redirect(url_for('create.create_deck'))

        deck_uuid = str(uuid.uuid4())

        deck = Deck(collection_id=collection, uuid=deck_uuid, title=title, public=public,
                    edited=datetime.today())
        db_session.add(deck)
        db_session.commit()
        flash('Deck Saved!')
        return redirect(url_for('create.create_flashcard'))
    return render_template('create_deck.html')


@create.route('/flashcard/', methods=['GET', 'POST'])
@requires_login
def create_flashcard():
    db_session = Session()
    if request.method == 'POST':
        title = bleach.clean(request.form['title'])
        deck = bleach.clean(request.form['deck'])

        term = bleach.clean(request.form['term'], tags=allowed_tags, attributes=allowed_attributes,
                            styles=allowed_styles, protocols=['data'], strip=True)

        definition = bleach.clean(request.form['definition'], tags=allowed_tags, attributes=allowed_attributes,
                                  styles=allowed_styles, protocols=['data'], strip=True)
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

        flashcard = Flashcard(deck_id=deck, uuid=str(uuid.uuid4()), title=title, term=term, definition=definition,
                              edited=datetime.today())

        selected_deck = db_session.query(Deck).filter(Deck.id == deck).first()
        selected_deck.edited = datetime.today()
        db_session.add(flashcard)
        db_session.commit()

        flash('Flashcard Saved!')
        return redirect(url_for('view.view_deck', uuid=selected_deck.uuid))
    try:
        decks = db_session.query(Deck).all()
    except:
        decks = None
    return render_template('create_flashcard.html', decks=decks)
