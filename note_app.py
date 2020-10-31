from flask import Flask, request, render_template, redirect, url_for, flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User, Collection, Note
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
        user = db_session.query(User).filter(User.email == session['user']).first()
        collections = db_session.query(Collection).filter(Collection.user_id == user.id).all()
        return dict(collections=collections)
    except:
        return dict(collections=None)


@app.context_processor
def notes_processor():
    def get_notes(id):
        notes = db_session.query(Note).filter(Note.collection_id == id).all()
        return notes
    return dict(get_notes=get_notes)


@app.route('/', methods=['GET'])
def root():
    if session.get('logged_in'):
        return render_template('main.html')
    return redirect(url_for('auth.login'))


@app.route('/collection/<uuid>/')
@requires_login
def view_collection(uuid):
    user = db_session.query(User).filter(User.email == session['user']).first()
    collection = db_session.query(Collection).filter(Collection.user_id == user.id).filter(Collection.uuid == uuid).first()
    return render_template('view_collection.html', collection=collection)


@app.route('/note/<uuid>/')
@requires_login
def view_note(uuid):
    note = db_session.query(Note).filter(Note.uuid == uuid).first()
    return render_template('view_note.html', note=note)


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
        print('Today is' + str(datetime.today()))
        note = Note(collection_id=collection, uuid=str(uuid.uuid4()), title=title, content=data, public=False,
                    edited=datetime.today())
        db_session.add(note)
        db_session.commit()
        flash('Note Saved!')
        return redirect(url_for('root'))
    return render_template('create_note.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
