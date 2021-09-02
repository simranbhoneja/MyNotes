import uuid

from datetime import datetime, timedelta
from functools import wraps

from enum import unique
from os import name
from flask import Flask, render_template, request, redirect, flash, session, make_response
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import response
# pip install flask_wtf
from flask_wtf import CSRFProtect

db_user = "root"
db_pass = "3009"
db_name = "my_notes"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://{}:{}@localhost/{}".format(db_user, db_pass, db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '4edf0cb5-0f76-4558-8562-0b0c8117afb5'

db = SQLAlchemy(app)
csrf = CSRFProtect()
csrf.init_app(app)

class Users(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(256))
    name = db.Column(db.String(100))

    def __init__(self, username, password, name):
        self.username = username
        self.password = password
        self.name = name

    @staticmethod
    def exists(username) -> bool:
        user = Users.get_user_by_username(username)
        return user !=None

    @staticmethod
    def get_user_by_username(username):
        return Users.query.filter_by(username = username).first()

    def __str__(self):
        return f"{self.username}"


class Token(db.Model):

    EXPIRE_AFTER = timedelta(hours=24)

    id = db.Column(db.Integer(), primary_key=True)
    token = db.Column(db.String(256), unique=True, nullable=False)
    expires_At = db.Column(db.DateTime(), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id"), nullable=False)

    def __init__(self, user_id, token, expires_at) -> None:
        super().__init__()
        self.user_id = user_id
        self.token = token
        self.expires_At = expires_at
    
    @staticmethod
    def create_token(user_id):

        token = Token(user_id, uuid.uuid4(), datetime.now() + timedelta(minutes=30))
        db.session.add(token)
        db.session.commit()

        return token.token

    @staticmethod
    def is_valid(token):

        token_db = Token.query.filter_by(token=token).first()
        if token_db and token_db.expires_At > datetime.now():
            return True
        return False
    
    @staticmethod
    def get_user_id_from_token(token):
        token_db = Token.query.filter_by(token=token).first()
        if token_db:
            return token_db.user_id
        return None


def login_required(func):

    @wraps(func)
    def wrapper_func(*args, **kwargs):
        if 'user' in session:
            return func(*args, **kwargs)
        if request.cookies.get('token'):
            token = request.cookies.get('token')
            if(Token.is_valid(token)):
                user_id = Token.get_user_id_from_token(token)
                if(user_id):
                    session['user'] = user_id
                    return func(*args, **kwargs)

        flash("Please Login First", "warning")
        return redirect(url_for('login'))
    
    return wrapper_func


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        form = request.form
        name = form.get('name', None)
        username = form.get('username', None)
        password = form.get('password', None)
        if (username and name and password):
            if(not Users.exists(username)):
                password = generate_password_hash(password)
                user = Users(username, password, name)
                db.session.add(user)
                db.session.commit()
                flash(f"{username} registered.\nLogin to proceed", "success")
                return redirect(url_for("login"))
            else:
                flash(f"User with {username} already exists.", "danger")
                return redirect(url_for("register"))
        else:
            flash(f"Please fill all required details", "warning")
            return redirect(url_for("register"))
                 

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        form = request.form
        username = form.get('username', None)
        password = form.get('password', None)
        if(Users.exists(username)):
            user = Users.get_user_by_username(username)
            if(check_password_hash(user.password, password)):
                session['user'] = user.id
                flash("You are logged in", "success")
                response = make_response(redirect(url_for('index')))
                if(form.get('remember_me', None)):
                    token = Token.create_token(user.id)
                    response.set_cookie('token', token, max_age= 60 * 30)
                return response
            else:
                flash("Incorrect Password", "info")
                return redirect(url_for('login'))
        else:
            flash("Incorrect user credentials", "info")
            return redirect(url_for('login'))


@app.route("/logout")
@login_required
def logout():
    response = make_response(redirect(url_for('login')))
    if 'user' in session:
        user_id = session.pop('user')
        response.set_cookie('token', '', max_age=-1)
        db.session.execute("delete from token where user_id = :user_id", {"user_id": user_id})
        db.session.commit()

    flash("Logged out successfully", "success")
    return response


@app.route("/")
@login_required
def index():
    user_id = session.get('user', None)
    notes_sql = f"Select * from notes where deleted_at is null and user_id = {user_id}"
    notes = db.session.execute(notes_sql)
    # print(type(notes))
    # for note in notes:
    #     print(note)
    return render_template('index.html', notes = notes)


@app.route("/create", methods=['GET', 'POST'])
@login_required
def create():
    if not 'user' in session:
        flash("Please Login First", "warning")
        return redirect(url_for('login'))

    if request.method == 'GET':
        folders_sql = "Select * from folder"
        folders = db.session.execute(folders_sql)
        return render_template('create.html', folders = folders)
    elif request.method == 'POST':
        user_id = session.get('user', None)
        form = request.form
        params = {
            "title" : form['title'],
            "content" : form.get('title', ''),
            "folder_id" : form.get('folder_id', ''),
            "user_id" : user_id,
        }
        if not params['folder_id']:
            params['folder_id'] = None
        
        sql = f"insert into notes (`title`, `content`, `folder_id`, `user_id`) values(:title, :content, :folder_id, :user_id)"
        
        db.session.execute(sql, params)
        db.session.commit()
        return redirect(url_for('index'))


@app.route("/update/<int:id>", methods=['GET', 'POST'])
@login_required
def update(id):
    note_sql = "Select * from notes where id= :id and deleted_at is null"
    note = db.session.execute(note_sql, {"id":id}).fetchone()
        
    if not note:
        return redirect(url_for('error', code=404))

    user_id = session.get('user', None)
    if note.user_id != user_id:
        return redirect(url_for('error', code=403))

    if request.method == 'GET':
        folders_sql = "Select * from folder"
        folders = db.session.execute(folders_sql)
        
        return render_template('update.html', folders = folders, note = note)
    
    elif request.method == 'POST':
        form = request.form
        params = {
            "title" : form['title'],
            "content" : form.get('content', ''),
            "folder_id" : form.get('folder_id', ''),
            "id": id,
        }
        if not params['folder_id']:
            params['folder_id'] = None
        
        sql = f"update notes set title=:title, content=:content, folder_id=:folder_id where id=:id"
        
        res = db.session.execute(sql, params)
        db.session.commit()
        return redirect(url_for('index'))


@app.route("/delete", methods=['POST'])
@login_required
def delete():
    if request.method == 'POST':
        try:
            id = request.form.get('id', None)
            if not id:
                return redirect('error', code=404)

            user_id = session.get('user', None)
            note_sql = "Select * from notes where id= :id and deleted_at is null"
            note = db.session.execute(note_sql, {"id":id}.fetchone())
            
            if not note:
                return redirect(url_for('error', code=404))
            if note.user_id != user_id:
                return redirect(url_for('error', code=403))

            sql = f"update notes set deleted_at = now() where id=:id"
            db.session.execute(sql, {"id": id})
            db.session.commit()

        except (Exception):
            return redirect(url_for('error', code=404))
        return redirect(url_for('index'))


@app.route("/error/<code>")
def error(code):
    codes = {
        "403": "403 Forbidden",
        "404": "404 Not Found",
    }
    return render_template("error.html", message = codes.get(code, "Invalid Request"))


@app.route("/thrash")
def thrash():
    pass


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)