from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from functools import wraps
from models import User
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import bleach
from dotenv import load_dotenv
import os

authentication = Blueprint('auth', __name__, url_prefix='/account/', template_folder='templates')

BASEDIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.curdir)
load_dotenv(os.path.join(PARENT_DIR, '.env'))
db_host = os.getenv("DATABASE_HOST")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
db_name = os.getenv("DATABASE_NAME")
database_uri = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'


engine = create_engine(database_uri)

Session = sessionmaker(bind=engine)


def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('logged_in', False)
        if not status:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@authentication.route('/', methods=['GET', 'POST'])
@requires_login
def account():
    db_session = Session()
    user = db_session.query(User).filter(User.email == session['user']).first()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email:
            user.email = bleach.clean(email)
            db_session.commit()
            session['user'] = bleach.clean(email)
            flash('Email saved')
            return redirect(url_for('auth.account'))

        if password:
            hashed = bcrypt.hashpw(bleach.clean(password).encode('utf-8'), bcrypt.gensalt())
            user.password = hashed
            db_session.commit()
            flash('Password saved')
            return redirect(url_for('auth.account'))

    return render_template('account.html', user=user)


@authentication.route('/register/', methods=['GET', 'POST'])
def register():
    db_session = Session()
    if request.method == 'POST':
        try:
            email = bleach.clean(request.form['email'])
            password = bleach.clean(request.form['password'])

            if not email:
                flash('Missing email')
                return redirect(url_for('auth.register'))
            if not password:
                flash('Missing password')
                return redirect(url_for('auth.register'))

            user = db_session.query(User).filter(User.email == email).count()

            if user >= 1:
                flash('Account  already exists')
                return redirect(url_for('auth.register'))
            else:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                user = User(email=email, password=hashed)
                db_session.add(user)
                db_session.commit()
            flash(f'Account {email} registered!')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            flash('Provide an Email and Password')
            return redirect(url_for('auth.register'))

    return render_template('register.html')


@authentication.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = bleach.clean(request.form['email'])
            password = bleach.clean(request.form['password'])

            if not email:
                flash('Missing email')
                return redirect(url_for('auth.login'))
            if not password:
                flash('Missing password')
                return redirect(url_for('auth.login'))

            if check_auth(email, password):
                session['logged_in'] = True
                session['user'] = email
                flash(f'Logged in, Welcome {email}!')
                return redirect(url_for('root'))
            else:
                flash('Invalid Login Info!')
                return redirect(url_for('auth.login'))
        except IntegrityError:
            flash('Provide an Email and Password')
            return redirect(url_for('auth.login'))
    return render_template('login.html')


@authentication.route('/logout/')
def logout():
    session['logged_in'] = False
    session.pop('user', None)
    flash('Logged out')
    return redirect(url_for('root'))


def check_auth(email, password):
    db_session = Session()
    try:
        user = db_session.query(User).filter(User.email == email).first()
        check = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

        if check:
            return True
        return False
    except:
        flash("User doesn't exist, have you registeared?")
        return False
