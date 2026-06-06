import requests

SERVER = "https://sunny-conor-premorse.ngrok-free.dev"
def log_in(login):

    data={"username": login}
    response = requests.post(f"{SERVER}/login", json=data)
    token=response.json().get("token")
    return token

def create_room(token):
    data={"token": token}
    response = requests.post(f"{SERVER}/create_room", json=data)
    room_id=response.json().get("roomid")

    return room_id
def get_rooms(token):
    data={"token": token}
    response = requests.post(f"{SERVER}/get_rooms", json=data)
    print(response.json())
    return response.json().get("rooms")

def join_room(token,room_id):
    data={"token": token, "roomid": room_id}
    response = requests.post(f"{SERVER}/join_room", json=data)
    return response.json()

def poll_host_room(token,room_id):
    data={"token": token, "roomid": room_id}
    response = requests.post(f"{SERVER}/poll_room", json=data)
    print(response.json())
    response=response.json()
    return response["player2"]!=None
def poll_start_game(token,room_id):
    data={"token": token, "roomid": room_id}
    response = requests.post(f"{SERVER}/poll_start_game", json=data)
    print(response.json())
    return response.json()
def start_game(token,room_id,host_color,settings):
    data={"token": token, "roomid": room_id, "host color": host_color, "settings": settings}
    response = requests.post(f"{SERVER}/start_game", json=data)
    print(response.json())
    response=response.json()
    return response["status"]=="ok"
def make_move(token,room_id,move):
    data={"token": token, "roomid": room_id, "move": move}
    response = requests.post(f"{SERVER}/move", json=data)
    print(response.json())
    response=response.json()
    return response["status"]=="ok"
def poll_move(token,room_id):
    data={"token": token, "roomid": room_id}
    response = requests.post(f"{SERVER}/poll_move", json=data)
    print(response.json())
    response=response.json()
    return response.get("move")
