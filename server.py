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
    print(f"User {username} logged in with token {token}")
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
        print(f"Invalid token: {token}",tokens)
        return jsonify({"status": "error", "message": "Invalid token"})
    room_id=data.get("roomid")
    if room_id not in rooms:
        print(f"Invalid room ID: {room_id}", rooms)
        return jsonify({"status": "error", "message": "Invalid room ID"})

    return jsonify({"status": "ok", "player2": rooms[room_id]["player2"],"player1": rooms[room_id]["player1"]})

@app.route("/poll_start_game", methods=["POST"])
def poll_start_game():
    data = request.get_json()
    token = data.get("token")
    print(f"Polling start game for token: {token}, room_id: {data.get('roomid')}")
    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})
    room_id=data.get("roomid")
    if room_id not in games:
        return jsonify({"status": "game not ready", })

    return jsonify({"status": "ok", "player1": games[room_id]["player1"],"player2": games[room_id]["player2"],"p1 color":games[room_id]["player1 color"],
                   "p2 color":games[room_id]["player2 color"], "settings": games[room_id]["settings"]})


@app.route("/start_game", methods=["POST"])
def start_game():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    room_id=data.get("roomid")
    if room_id not in rooms:
        return jsonify({"status": "error", "message": "Invalid room ID"})

    games[room_id]={"state":"started", "player1": rooms[room_id]["player1"], "player2": rooms[room_id]["player2"],"settings":data.get("settings")}

    host_color=data.get("host color")

    games[room_id]["player1 color"]=host_color
    games[room_id]["player2 color"]="Black" if host_color=="White" else "White"

    games[room_id]["turn"]="Black"
    games[room_id]["move"]=None
    games[room_id]["pass"]=False

    rooms.pop(room_id)

    return jsonify({"status": "ok",})

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    game_id = data.get("gameid")
    if game_id not in games:
        return jsonify({"status": "error", "message": "Invalid game ID"})
    games[game_id]["move"]=data.get("move")
    games[game_id]["turn"]="Black" if games[game_id]["turn"]=="White" else "White"
    return jsonify({"status": "ok" })

@app.route("/poll_move", methods=["POST"])
def poll_move():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    game_id = data.get("gameid")
    if game_id not in games:
        return jsonify({"status": "error", "message": "Invalid game ID"})
    if games[game_id]["turn"]!=data.get("color"):
        return jsonify({"status": "ok", "move": None})

    move=games[game_id]["move"]
    games[game_id]["move"]=None

    passt=games[game_id]["pass"]
    games[game_id]["pass"]=False

    return jsonify({"status": "ok" ,"move":move,"pass":passt})


@app.route("/pass_turn", methods=["POST"])
def pass_turn():
    data = request.get_json()
    token = data.get("token")

    if token not in tokens:
        return jsonify({"status": "error", "message": "Invalid token"})

    game_id = data.get("gameid")
    if game_id not in games:
        return jsonify({"status": "error", "message": "Invalid game ID"})

    games[game_id]["pass"]=True
    return jsonify({"status": "ok" })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)