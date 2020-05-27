from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku

import random
import string

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://jwvgoesyetehzt:6e011fd4118f8fd0157b386251b52016f639a38f57db1b01824928e9c10826c2@ec2-35-171-31-33.compute-1.amazonaws.com:5432/det8jjb7qejlel"

db = SQLAlchemy(app)
ma = Marshmallow(app)
heroku = Heroku(app)
CORS(app)


class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    users = db.relationship("User", cascade="all,delete", backref="session", lazy=True)
    buzzer_lists = db.relationship("BuzzerList", cascade="all,delete", backref="session", lazy=True)

    def __init__(self, name):
        self.name = name

class SessionSchema(ma.Schema):
    class Meta:
        fields = ("id", "name")

session_schema = SessionSchema()
sessions_schema = SessionSchema(many=True)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    is_host = db.Column(db.Boolean, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    buzzer_lists = db.relationship("BuzzerList", cascade="all,delete", backref="user", lazy=True)

    def __init__(self, name, is_host, session_id):
        self.name = name
        self.is_host = is_host
        self.session_id = session_id

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "is_host", "session_id")

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class BuzzerList(db.Model):
    __tablename__ = "buzzer_list"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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

    session_name = ""
    while True:
        session_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase) for _ in range(5))
        session_check = db.session.query(Session).filter(Session.name == session_name).all()
        if len(session_check) == 0:
            break

    session = Session(session_name)
    db.session.add(session)
    db.session.commit()
    
    session_host = User(user_name, True, session.id)
    db.session.add(session_host)
    db.session.commit()

    info = {
        "session": session_schema.dump(session),
        "user": user_schema.dump(session_host)
    }

    return jsonify(info)

@app.route("/session/get", methods=["GET"])
def get_all_sessions():
    all_sessions = db.session.query(Session).all()
    return jsonify(sessions_schema.dump(all_sessions))

@app.route("/session/get/<id>", methods=["GET"])
def get_session(id):
    session = db.session.query(Session).filter(Session.id == id).first()
    return jsonify(session_schema.dump(session))

@app.route("/session/get/name/<name>", methods=["GET"])
def get_session_by_name(name):
    session = db.session.query(Session).filter(Session.name == name).first()
    return jsonify(session_schema.dump(session))

@app.route("/session/get/host/<id>", methods=["GET"])
def get_session_host(id):
    host = db.session.query(User).filter(User.session_id == id and User.is_host == True).first()
    return jsonify(user_schema.dump(host))

@app.route("/session/delete/<id>", methods=["DELETE"])
def delete_session(id):
    session = db.session.query(Session).filter(Session.id == id).first()
    db.session.delete(session)
    db.session.commit()
    return jsonify("Session Deleted")

@app.route("/user/create", methods=["POST"])
def create_user():
    post_data = request.get_json()
    user_name = post_data.get("name")
    session_id = post_data.get("session_id")

    user = User(user_name, False, session_id)
    db.session.add(user)
    db.session.commit()

    return jsonify(user_schema.dump(user))

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/user/get/<id>", methods=["GET"])
def get_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route("/user/get/session/<id>")
def get_users_by_session(id):
    all_users = db.session.query(User).filter(User.session_id == id).all()
    return jsonify(users_schema.dump(all_users))


@app.route("/buzzer_list/add", methods=["POST"])
def add_buzzer():
    post_data = request.get_json()
    session_id = post_data.get("session_id")
    user_id = post_data.get("user_id")

    buzzer_check = db.session.query(BuzzerList).filter(BuzzerList.session_id == session_id).filter( BuzzerList.user_id == user_id).all()
    print(buzzer_check)
    if len(buzzer_check) == 0:
        buzzer = BuzzerList(session_id, user_id)
        db.session.add(buzzer)
        db.session.commit()

        return jsonify("Buzzer Added")
    
    return jsonify("Buzzer already exists, aborting...")

@app.route("/buzzer_list/get")
def get_all_buzzers():
    buzzers = db.session.query(BuzzerList).all()
    return jsonify(buzzer_lists_schema.dump(buzzers))

@app.route("/buzzer_list/get/<id>")
def get_buzzer(id):
    buzzers = db.session.query(BuzzerList).filter(BuzzerList.id == id).first()
    return jsonify(buzzer_list_schema.dump(buzzers))

@app.route("/buzzer_list/get/session/<id>")
def get_buzzers_by_session(id):
    all_buzzers = db.session.query(BuzzerList).filter(BuzzerList.session_id == id).all()
    return jsonify(buzzer_lists_schema.dump(all_buzzers))

@app.route("/buzzer_list/get/usernames/session/<id>")
def get_buzzer_usernames_by_session(id):
    all_buzzers = db.session.query(BuzzerList.user_id).filter(BuzzerList.session_id == id).all()
    users = []

    for user_id in all_buzzers:
        user = db.session.query(User.name).filter(User.id == user_id).first()
        users.append(user[0])

    return jsonify(users)

@app.route("/buzzer_list/delete/session/<id>", methods=["DELETE"])
def delete_buzzers_by_session(id):
    all_buzzers = db.session.query(BuzzerList).filter(BuzzerList.session_id == id).all()

    for buzzer in all_buzzers:
        db.session.delete(buzzer)

    db.session.commit()

    return jsonify("Buzzers Deleted")


if __name__ == "__main__":
    app.run(debug=True)