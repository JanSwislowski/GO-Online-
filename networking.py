import requests
from setup import running, incoming_queue, outgoing_queue
import time
from client import *
SERVER_URL = "https://yourserver.com"

ticks=2
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

            elif action["type"]=="poll host room":
                player2_joined=poll_host_room(action["token"], action["room_id"])
                incoming_queue.put({"type": "poll_host_response", "player2_joined": player2_joined})

            elif action["type"]=="get rooms":
                rooms=get_rooms(action["token"])
                incoming_queue.put({"type": "rooms_list", "rooms": rooms})

            elif action["type"]=="join room":
                resp_json=join_room(action["token"], action["room_id"])
                incoming_queue.put({"type": "join_room_response", "response": resp_json})

            elif action["type"]=="start game":
                success=start_game(action["token"], action["room_id"], action["host_color"], action["settings"])
                incoming_queue.put({"type": "start_game_response", "success": success})

            elif action["type"]=="poll start game":
                resp_json=poll_start_game(action["token"], action["room_id"])
                incoming_queue.put({"type": "poll_start_game_response", "response": resp_json})

            elif action["type"]=="make move":
                success=make_move(action["token"], action["room_id"], action["move"])
                incoming_queue.put({"type": "make_move_response", "success": success})

            elif action["type"]=="poll move":
                move=poll_move(action["token"], action["room_id"], action["color"])
                incoming_queue.put({"type": "poll_move_response", "move": move})

        time.sleep(1/ticks)