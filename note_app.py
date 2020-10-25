from flask import Flask, request, render_template, redirect, url_for, flash, session
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models import User


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
                session['email'] = email
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
    session.pop('email', None)
    flash('Logged out')
    return redirect(url_for('root'))


def check_auth(email, password):
    user = db_session.query(User).filter(User.email == email).first()
    hashed_input = bcrypt.hashpw(password.encode('utf-8'), user.password)
    if hashed_input == user.password:
        return True
    return False


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
