import requests
from setup import running, incoming_queue, outgoing_queue
import time
from client import *
SERVER_URL = "https://yourserver.com"

ticks=1
def network_loop():

    while running:
        # Send outgoing actions
        while not outgoing_queue.empty():
            action = outgoing_queue.get()
            if action["type"]=="login":
                token=log_in(action["username"])
                incoming_queue.put({"type": "logged_in", "token": token})
            elif action["type"]=="create room":
                room_id=create_room(action["token"])
                incoming_queue.put({"type": "room_created", "room_id": room_id})
            elif action["type"]=="get rooms":
                rooms=get_rooms(action["token"])
                incoming_queue.put({"type": "rooms_list", "rooms": rooms})
            elif action["type"]=="join room":
                resp_json=join_room(action["token"], action["room_id"])
                incoming_queue.put({"type": "join_room_response", "response": resp_json})

        time.sleep(1/ticks)