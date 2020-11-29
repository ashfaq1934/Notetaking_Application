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

# Register as blueprint
authentication = Blueprint('auth', __name__, url_prefix='/account/', template_folder='templates')

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

# Flask view decorator to return the user to the login page if they aren't authenticated
def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('logged_in', False)
        if not status:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# Flask decorator for the user's account page
@authentication.route('/', methods=['GET', 'POST'])
@requires_login
def account():
    # Create database session and get the authenticated user's details
    db_session = Session()
    user = db_session.query(User).filter(User.email == session['user']).first()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # If the email was changed, sanitize the input and modify the User object
        if email:
            user.email = bleach.clean(email)
            db_session.commit()
            session['user'] = bleach.clean(email)
            flash('Email saved')
            return redirect(url_for('auth.account'))
        # If the password was changed, sanitize the input and modify the User object
        if password:
            hashed = bcrypt.hashpw(bleach.clean(password).encode('utf-8'), bcrypt.gensalt())
            user.password = hashed
            db_session.commit()
            flash('Password saved')
            return redirect(url_for('auth.account'))

    return render_template('account.html', user=user)


# Flask decorator for registration page
@authentication.route('/register/', methods=['GET', 'POST'])
def register():
    # Create database session
    db_session = Session()
    if request.method == 'POST':
        try:
            # Sanitize inputs
            email = bleach.clean(request.form['email'])
            password = bleach.clean(request.form['password'])
            # if email or password is empty, redirect back to registration page
            if not email:
                flash('Missing email')
                return redirect(url_for('auth.register'))
            if not password:
                flash('Missing password')
                return redirect(url_for('auth.register'))
            # Query User table for existing users with the same email, and if they exist, redirect back to registration
            user = db_session.query(User).filter(User.email == email).count()
            if user >= 1:
                flash('Account  already exists')
                return redirect(url_for('auth.register'))
            else:
                # If the user doesnt exist, create a new one with the email and password input field
                # Hash and salt the password before commit the user to the database
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


# Flask decorator login page
@authentication.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Sanitize inputs
            email = bleach.clean(request.form['email'])
            password = bleach.clean(request.form['password'])
            # if email or password is empty, redirect back to login page
            if not email:
                flash('Missing email')
                return redirect(url_for('auth.login'))
            if not password:
                flash('Missing password')
                return redirect(url_for('auth.login'))
            # Use check_auth method to check if the credentials match, if the method returns true, create the session
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


# Flask route for logout
# Delete session and redirect to root page
@authentication.route('/logout/')
def logout():
    session['logged_in'] = False
    session.pop('user', None)
    flash('Logged out')
    return redirect(url_for('root'))


# Method for checking if the login form input matches the user's credentials
def check_auth(email, password):
    # Create database session
    db_session = Session()
    try:
        # Query the User table and filter the objects by the inputted email
        user = db_session.query(User).filter(User.email == email).first()
        # Use bcrypt's check password method to hash the password input and see if they match
        check = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

        # If the check passes return true, otherwise return false
        if check:
            return True
        return False
    except:
        # If the user query fails, return false
        flash("User doesn't exist, have you registered?")
        return False
