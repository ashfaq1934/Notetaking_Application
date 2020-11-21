from flask import Flask, request, render_template, session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import User, Collection, Note, Deck
from authentication.auth import authentication, requires_login
from view.view import view
from public.public import public
from create.create import create
from edit.edit import edit
from delete.delete import delete
from dotenv import load_dotenv
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY")
app.register_blueprint(authentication)
app.register_blueprint(view)
app.register_blueprint(public)
app.register_blueprint(create)
app.register_blueprint(edit)
app.register_blueprint(delete)


db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
database_uri = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
print(BASEDIR)
print(database_uri)
print('-------------------------------------------------')
engine = create_engine(database_uri)


Session = sessionmaker(bind=engine, autocommit=True)


@app.context_processor
def get_collections():
    db_session = Session()
    try:
        collections = db_session.query(Collection).join(User, Collection.user_id == User.id) \
            .filter(User.email == session['user']).all()
        return dict(collections=collections)
    except:
        return dict(collections=None)


@app.context_processor
def resources_processor():
    def get_resources(id):
        db_session = Session()
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
    db_session = Session()
    notes = db_session.query(Note).join(Collection, Note.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user'])\
        .order_by(desc('edited')).limit(3).all()

    decks = db_session.query(Deck).join(Collection, Deck.collection_id == Collection.id) \
        .join(User, Collection.user_id == User.id).filter(User.email == session['user']) \
        .order_by(desc('edited')).limit(3).all()

    return render_template('main.html', notes=notes, decks=decks)


@app.route('/browse/', methods=['GET'])
def browse():
    db_session = Session()
    query = request.args.get('query')
    if query:
        search = "%{}%".format(query)
        searched_notes = db_session.query(Note).filter(Note.public == True).filter(Note.title.like(search)).all()
        searched_decks = db_session.query(Deck).filter(Deck.public == True).filter(Deck.title.like(search)).all()
        searched_collections = db_session.query(Collection).filter(Collection.public == True)\
            .filter(Collection.title.like(search)).all()

    else:
        searched_notes = None
        searched_decks = None
        searched_collections = None
    return render_template('browse.html', searched_notes=searched_notes, searched_decks=searched_decks,
                           searched_collections=searched_collections)


@app.route('/search/', methods=['GET'])
def search():
    db_session = Session()
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
