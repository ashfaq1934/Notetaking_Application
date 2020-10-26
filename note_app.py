from flask import Flask, request, render_template, redirect, url_for, flash, session
from functools import wraps
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User, Collection
import uuid


app = Flask(__name__, static_folder="static")
app.secret_key = 'A0Zr98j/3yXR~XHH!jmN]LWX/,?RT'
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False}, echo=True)

Session = sessionmaker(bind=engine)
db_session = Session()

# Todo: implement input sanitization


@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            if not email:
                flash('Missing email')
                return redirect(url_for('register'))
            if not password:
                flash('Missing password')
                return redirect(url_for('register'))

            user = db_session.query(User).filter(User.email == email).count()

            if user >= 1:
                flash('Account  already exists')
                return redirect(url_for('register'))
            else:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                user = User(email=email, password=hashed)
                db_session.add(user)
                db_session.commit()
            flash(f'Account {email} registered!')
            return redirect(url_for('root'))
        except IntegrityError:
            flash('Provide an Email and Password')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            if not email:
                flash('Missing email')
                return redirect(url_for('login'))
            if not password:
                flash('Missing password')
                return redirect(url_for('login'))

            if check_auth(email, password):
                session['logged_in'] = True
                session['user'] = email
                flash(f'Logged in, Welcome {email}!')
                return redirect(url_for('root'))
            else:
                flash('Invalid Login Info!')
                return redirect(url_for('login'))
        except IntegrityError:
            flash('Provide an Email and Password')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout/')
def logout():
    session['logged_in'] = False
    session.pop('user', None)
    flash('Logged out')
    return redirect(url_for('root'))


def check_auth(email, password):
    user = db_session.query(User).filter(User.email == email).first()
    hashed_input = bcrypt.hashpw(password.encode('utf-8'), user.password)
    if hashed_input == user.password:
        return True
    return False


def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('logged_in', False)
        if not status:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/create/collection/', methods=['GET', 'POST'])
@requires_login
def create_collection():
    if request.method == 'POST':
        try:
            title = request.form['title']
            if not title:
                flash('Provide a title')
                return redirect(url_for('create_collection'))
            user = db_session.query(User).filter(User.email == session['user']).first()
            collection = Collection(user_id=user.id, uuid=str(uuid.uuid4()), title=title, public=False)
            db_session.add(collection)
            db_session.commit()

        except IntegrityError:
            flash('Provide a title')
            return redirect(url_for('create_collection'))

    return render_template('create_collection.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
