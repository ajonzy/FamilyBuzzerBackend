from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_heroku import Heroku

import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'development key'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
heroku = Heroku(app)


connection_list = {}
session_list = {}


@app.route("/", methods=["GET"])
def home():
    return jsonify({"Connections": connection_list, "Sessions": session_list})


@socketio.on('connect')
def on_connect():
    connection_list[request.sid] = {"type": "", "session": "", "name": ""}
    print('user connected')
    print(request.sid)
    print(connection_list)
    print(session_list)

@socketio.on('disconnect')
def on_disconnect():
    print('user disconnected')
    print(request.sid)

    connection = connection_list[request.sid]

    if connection["type"] == "host":
        session_list.pop(connection["session"])
        emit("host_disconnect", {"session": connection["session"]}, broadcast=True)
    elif connection["type"] == "user":
        if connection["name"] in session_list.get(connection["session"])["users"]:
            session_list.get(connection["session"])["users"].remove(connection["name"])

    connection_list.pop(request.sid)
    print(connection_list)
    print(session_list)

@socketio.on('host_user')
def add_host(data):
    session_name = ""
    while True:
        session_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase) for _ in range(5))
        session_check = session_list.get(session_name, -1)
        if session_check == -1:
            break

    connection_list[request.sid] = {"type": "host", "session": session_name, "name": data.get("host")}
    session_list[session_name] = {"host": data.get("host"), "users": [], "buzz_list": []}
    emit("session_created", {"session": session_name})

@socketio.on("get_buzzers")
def get_buzzers(data):
    emit("buzzers", {
        "session": data.get("session"),
        "buzz_list": session_list[data.get("session")]["buzz_list"]
        })

@socketio.on("clear_buzzers")
def clear_buzzers(data):
    session_list[data.get("session")]["buzz_list"] = []
    emit("buzzers_cleared", {"session": data.get("session")}, broadcast=True)

@socketio.on("join_session")
def join_session(data):
    if data.get("name") in session_list.get(data.get("session"), {}).get("users", []):
        emit("name_taken")
    else:
        connection_list[request.sid] = {"type": "user", "session": data.get("session"), "name": data.get("name")}
        session_list.get(data.get("session"), {}).get("users", []).append(data.get("name"))
        emit("session_data", {"session_data": session_list.get(data.get("session"), -1)})

@socketio.on("buzz")
def handle_buzz(data):
    if data.get("name") not in session_list[data.get("session")]["buzz_list"]:
        session_list[data.get("session")]["buzz_list"].append(data.get("name"))
        emit("new_buzz", {"session": data.get("session"), "buzz_list": session_list[data.get("session")]["buzz_list"]}, broadcast=True)
        emit("buzz_added", {"session": data.get("session"), "buzz_list": session_list[data.get("session")]["buzz_list"]})


if __name__ == "__main__":
    socketio.run(app, debug=True)