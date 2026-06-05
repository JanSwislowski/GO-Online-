from app import App
from networking import network_loop
import threading

if __name__ == "__main__":
    network_thread = threading.Thread(
        target=network_loop,
        daemon=True
    )
    app = App()
    network_thread.start()
    app.run()