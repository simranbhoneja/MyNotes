from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

db_user = "root"
db_pass = "3009"
db_name = "my_notes"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://{}:{}@localhost/{}".format(db_user, db_pass, db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

@app.route("/")
def index():
    notes_sql = "Select * from notes"
    notes = db.session.execute(notes_sql)
    print(type(notes))
    for note in notes:
        print(note)
    return render_template('index.html', notes = notes)


if __name__ == "__main__":
    app.run(debug=True)