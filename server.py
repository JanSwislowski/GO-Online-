from flask import Flask, request, jsonify
import secrets

app = Flask(__name__)

tokens={}
rooms={}

games={}

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")

    token = secrets.token_hex(16)
    tokens[token]=username
    return jsonify({"status": "ok", "token": token})

@app.route("/create_room", methods=["POST"])
def create_room():
    data = request.get_json()

    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    room_id = secrets.token_hex(8)

    rooms[room_id] = {"host": tokens[token], "player1": tokens[token], "player2": None}
    return jsonify({"status": "ok", "roomid": room_id})

@app.route("/get_rooms", methods=["POST"])
def get_rooms():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})
    avaible_rooms = {room_id: info for room_id, info in rooms.items() if info["player2"] is None}
    return jsonify({"status": "ok", "rooms": avaible_rooms})

@app.route("/join_room", methods=["POST"])
def join_room():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})
    room_id=data.get("roomid")
    if room_id not in rooms:
        return jsonify({"status": "error", "message": "Invalid room ID"})
    if rooms[room_id]["player2"] is not None:
        return jsonify({"status": "error", "message": "Room is full"})

    rooms[room_id]["player2"]=tokens[token]
    return jsonify({"status": "ok", "message": f"Joined room", "roomid": room_id})

@app.route("/poll_room", methods=["POST"])
def poll_room():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})
    room_id=data.get("roomid")
    if room_id not in rooms:
        return jsonify({"status": "error", "message": "Invalid room ID"})

    return jsonify({"status": "ok", "player2": rooms[room_id]["player2"]})

@app.route("/start_game", methods=["POST"])
def start_game():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    room_id=data.get("roomid")
    if room_id not in rooms:
        return jsonify({"status": "error", "message": "Invalid room ID"})
    games[room_id]={"player1": rooms[room_id]["player1"], "player2": rooms[room_id]["player2"]}
    rooms.pop(room_id)
    return jsonify({"status": "ok"})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)