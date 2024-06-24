import socket
from _thread import *
from game_state import GameState
import pickle
import keyboard
import time

MAX_CONNECTIONS = 2
PORT = 5555

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

server = get_ip()
print("Server IP: " + server)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, PORT))
except socket.error as e:
    str(e)

s.listen(MAX_CONNECTIONS)
print("Server started, waiting for connection")

game_state = GameState()

def threaded_server_control():
    global game_state

    print("Game ready, press s to start")

    while True:

        if keyboard.is_pressed("s"):
            if game_state.state == game_state.IDLE:
                print("Game starting")
                game_state.state = game_state.STARTING
                game_state.time_in_state = game_state.STARTUP_TIME
                game_state.state_start_time = time.time()

                game_state.remaining_play_time = game_state.state_start_time + game_state.time_in_state - time.time()

        if game_state.state == game_state.STARTING:
            if time.time() > game_state.state_start_time + game_state.time_in_state:
                print("Game running")
                game_state.state = game_state.RUNNING
                game_state.time_in_state = game_state.PLAY_TIME
                game_state.state_start_time = time.time()

            game_state.remaining_play_time = game_state.state_start_time + game_state.time_in_state - time.time()

        if game_state.state == game_state.TIMEOUT:
            if time.time() > game_state.state_start_time + game_state.time_in_state:
                print("Timeout over")
                game_state.state = game_state.RUNNING
                game_state.time_in_state = game_state.save_remaining_play_time
                game_state.state_start_time = time.time()

            game_state.remaining_play_time = game_state.state_start_time + game_state.time_in_state - time.time()

        if game_state.state == game_state.RUNNING:

            game_state.remaining_play_time = game_state.state_start_time + game_state.time_in_state - time.time()

            if time.time() > game_state.state_start_time + game_state.time_in_state:
                print("Game ended")
                game_state.state = game_state.ENDED
                game_state.time_in_state = game_state.ENDED_TIME
                game_state.state_start_time = time.time()
                game_state.remaining_play_time = 0

        if game_state.state == game_state.ENDED:
            if time.time() > game_state.state_start_time + game_state.time_in_state:
                print("Game ready, press s to start")
                game_state.state = game_state.IDLE

        time.sleep(0.01)

start_new_thread(threaded_server_control, ())

def threaded_client(conn, player):
    conn.send(str.encode(str(player)))
    reply = ""
    while True:
        try:
            update = pickle.loads(conn.recv(2048))

            if not update:
                print("Disconnected")
                break
            else:
                if (game_state.player_best[player] == -1 and update.best_score != -1) or game_state.player_best[player] > update.best_score:
                    print("Got new score {} for player {}".format(update.best_score, player))
                    game_state.player_best[player] = update.best_score

                if update.timeout == True and game_state.player_timeout[player] > 0:
                    print("Timeout by player {}".format(player))
                    game_state.player_timeout[player] -= 1
                    game_state.state = game_state.TIMEOUT
                    game_state.save_remaining_play_time = game_state.state_start_time + game_state.time_in_state - time.time()
                    game_state.time_in_state = game_state.TIMEOUT_TIME
                    game_state.state_start_time = time.time()

                if update.joker == True and game_state.player_joker[player] > 0:
                    print("Phone joker by player {}".format(player))
                    print("GO AND HELP THEM!!!")
                    game_state.player_joker[player] -= 1

            conn.sendall(pickle.dumps(game_state))
        except:
            break

    print("Lost connection")
    conn.close()

currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1
