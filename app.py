from enum import unique
from os import name
from flask import Flask, render_template, request, redirect
from flask.helpers import flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import session
from werkzeug.security import generate_password_hash

db_user = "root"
db_pass = "3009"
db_name = "my_notes"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://{}:{}@localhost/{}".format(db_user, db_pass, db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '4edf0cb5-0f76-4558-8562-0b0c8117afb5'

db = SQLAlchemy(app)

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
        user = Users.query.filter_by(username = username).first()
        return user !=None

    def __str__(self):
        return f"{self.username}"

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
    return render_template('login.html')

@app.route("/")
def index():
    notes_sql = "Select * from notes where deleted_at is null"
    notes = db.session.execute(notes_sql)
    # print(type(notes))
    # for note in notes:
    #     print(note)
    return render_template('index.html', notes = notes)

@app.route("/create", methods=['GET', 'POST'])
def create():

    if request.method == 'GET':
        folders_sql = "Select * from folder"
        folders = db.session.execute(folders_sql)
        return render_template('create.html', folders = folders)
    elif request.method == 'POST':

        form = request.form
        params = {
            "title" : form['title'],
            "content" : form.get('title', ''),
            "folder_id" : form.get('folder_id', ''),
        }
        if not params['folder_id']:
            params['folder_id'] = None
        
        sql = f"insert into notes (`title`, `content`, `folder_id`) values(:title, :content, :folder_id)"
        
        db.session.execute(sql, params)
        db.session.commit()
        return redirect(url_for('index'))

@app.route("/update/<int:id>", methods=['GET', 'POST'])
def update(id):
    if request.method == 'GET':
        folders_sql = "Select * from folder"
        folders = db.session.execute(folders_sql)
        note_sql = "Select * from notes where id= :id and deleted_at is null"
        note = db.session.execute(note_sql, {"id":id}).fetchone()
        
        if not note:
            return redirect(url_for('error', code=404))
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
def delete(id):
    if request.method == 'POST':
        try:
            id = request.form.get('id', None)
            if not id:
                return redirect('error', code=404)
            sql = f"update notes set deleted_at = now() where id=:id"
            db.session.execute(sql, {"id": id})
            db.session.commit()
        except (Exception):
            return redirect(url_for('error', code=404))
        return redirect(url_for('index'))

@app.route("/error/<code>")
def error(code):
    codes = {
        "404": "404 Not Found",
    }
    return render_template("error.html", message = codes.get(code, "Invalid Request"))

@app.route("/thrash")
def thrash():
    pass

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)