from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from functools import wraps
from models import User
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

authentication = Blueprint('auth', __name__, url_prefix='/account/', template_folder='templates')
engine = create_engine('sqlite:///database.db', connect_args={'check_same_thread': False}, echo=True)

Session = sessionmaker(bind=engine)
db_session = Session()


@authentication.route('/register/', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.login'))
        except IntegrityError:
            flash('Provide an Email and Password')
            return redirect(url_for('register'))

    return render_template('register.html')


@authentication.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

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
    try:
        user = db_session.query(User).filter(User.email == email).first()
        hashed_input = bcrypt.hashpw(password.encode('utf-8'), user.password)
        if hashed_input == user.password:
            return True
        return False
    except:
        flash("User doesn't exist, have you registered?")
        return False


def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('logged_in', False)
        if not status:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
