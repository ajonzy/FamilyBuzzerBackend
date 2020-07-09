from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'development key'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)


host_list = {}


@socketio.on('connect')
def on_connect():
    print('user connected')
    print(request.sid)
    print(host_list)

@socketio.on('disconnect')
def on_disconnect():
    print('user disconnected')
    print(request.sid)
    for host in host_list.values():
        if host["id"] == request.sid:
            host_list.pop(host["session"])
            break
    print(host_list)

@socketio.on('host_user')
def add_host(data):
    session_name = ""
    while True:
        session_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase) for _ in range(5))
        session_check = host_list.get(session_name, -1)
        if session_check == -1:
            break

    host_list[session_name] = {"id": request.sid, "session": session_name, "host": data.get("host"), "buzz_list": []}
    emit("session_created", {"session": session_name})

@socketio.on("get_buzzers")
def get_buzzers(data):
    emit("buzzers", {
        "session": data.get("session"),
        "buzz_list": host_list[data.get("session")]["buzz_list"]
        })

@socketio.on("clear_buzzers")
def clear_buzzers(data):
    host_list[data.get("session")]["buzz_list"] = []
    emit("buzzers_cleared", broadcast=True)

@socketio.on("join_session")
def join_session(data):
    emit("session_data", {"session_data": host_list.get(data.get("session"), -1)})

@socketio.on("buzz")
def handle_buzz(data):
    host_list[data.get("session")]["buzz_list"].append(data.get("name"))
    emit("new_buzz", {"session": data.get("session"), "buzz_list": host_list[data.get("session")]["buzz_list"]}, broadcast=True)
    emit("buzz_added", {"session": data.get("session"), "buzz_list": host_list[data.get("session")]["buzz_list"]})


if __name__ == "__main__":
    socketio.run(app, debug=True)