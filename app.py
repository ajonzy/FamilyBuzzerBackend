from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = ""

db = SQLAlchemy(app)
ma = Marshmallow(app)
heroku = Heroku(app)
CORS(app)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    users = db.relationship("User", backref="session", lazy=True)

    def __init__(self, name):
        self.name = name

class SessionSchema(ma.Schema):
    class Meta:
        fields = ("id", "name")

session_schema = SessionSchema()
sessions_schema = SessionSchema(many=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    is_host = db.Column(db.Boolean, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    buzzer_lists = db.relationship("BuzzerList", backref="user", lazy=True)

    def __init__(self, name, is_host, session_id):
        self.name = name
        self.is_host = is_host
        self.session_id = session_id

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "is_host", "session_id")

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class BuzzerList(db.model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String(), db.ForeignKey('user.name'), nullable=False)

    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id

class BuzzerListSchema(ma.Schema):
    class Meta:
        fields = ("id", "session_id", "user_id")

buzzer_list_schema = BuzzerListSchema()
buzzer_lists_schema = BuzzerListSchema(many=True)


@app.route("/session/create", methods=["POST"])
def create_session():
    post_data = request.get_json()
    user_name = post_data.get("name")

    session_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(5))

    session = Session(session_name)
    session_host = User(user_name, True, session.id)

    db.session.add(session)
    db.session.add(session_host)
    db.session.commit()

    return jsonify("Session Created")

@app.route("session/get", methods=["GET"])
def get_all_sessions():
    all_sessions = db.session.query(Session).all()
    return jsonify(sessions_schema.dump(all_sessions))


if __name__ == "__main__":
    app.run(debug=True)